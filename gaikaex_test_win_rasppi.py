# 外貨EXにChromeDriverでログインして、為替レートを取得するサンプルコード
# 事前にChromeDriverをインストールしておくこと

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from kill_process import force_kill_chrome_processes
from kill_process import kill_chrome
from kill_process import cleanup_driver_selective

from login_process import login_gaikaex
from place_order import (
    navigate_to_new_order,
    operate_realtime_order,
    operate_realtime_order_fast,
    operate_realtime_order_ultra_fast,
    operate_limit_order, 
    operate_ifd_order,
    operate_oco_order,
    operate_ifo_order,
    analyze_form_elements,
    get_order_frame_info,
    get_page_source_info,
)

import time
import os
import platform
import signal
import atexit
import sys

# グローバルドライバー変数（終了処理用）
global_driver = None

def cleanup_on_exit():
    """プログラム終了時の緊急クリーンアップ"""
    try:
        print("\n=== 緊急終了処理を実行 ===")
        if global_driver:
            global_driver.quit()
            print("✅ グローバルドライバーを終了しました")
    except:
        pass
    try:
        force_kill_chrome_processes()
        print("✅ 緊急強制終了処理完了")
    except:
        pass

# プログラム終了時の自動クリーンアップを登録
atexit.register(cleanup_on_exit)


# ドル/円レート監視処理（例：1秒ごとに取得して表示）
def monitor_usdjpy_rate(driver):
    import csv
    try:
        bid_list = []
        ask_list = []
        minute_start = None
        import os
        # CSVファイル名は記録開始日時を付与（最初に書き込むタイミングで決定）
        base_name = "usdjpy_rate_log"
        csv_file = None
        print("1分ごとにBid/Askの開始値・終値・最高値・最小値を記録します。Ctrl+Cで終了")
        while True:
            try:
                driver.switch_to.default_content()
                time.sleep(0.1)
                try:
                    priceboard_iframe = driver.find_element(By.CSS_SELECTOR, "iframe#priceboard,iframe[name='priceboard']")
                    driver.switch_to.frame(priceboard_iframe)
                    time.sleep(0.1)
                except Exception:
                    pass
                try:
                    board_iframe = driver.find_element(By.CSS_SELECTOR, "iframe#boardIframe,iframe[name='boardIframe']")
                    driver.switch_to.frame(board_iframe)
                    time.sleep(0.1)
                except Exception:
                    pass
                bid, ask = None, None
                # hidden input
                try:
                    bid = driver.find_element(By.ID, "bid2").get_attribute("value")
                    ask = driver.find_element(By.ID, "ask2").get_attribute("value")
                except Exception:
                    pass
                # ID要素
                if bid is None or ask is None:
                    try:
                        bid_main = driver.find_element(By.ID, "bidRate2").text.strip()
                        bid_small = driver.find_element(By.ID, "bidRateSmall2").text.strip()
                        ask_main = driver.find_element(By.ID, "askRate2").text.strip()
                        ask_small = driver.find_element(By.ID, "askRateSmall2").text.strip()
                        bid = f"{bid_main}.{bid_small}"
                        ask = f"{ask_main}.{ask_small}"
                    except Exception:
                        pass
                # JS
                if bid is None or ask is None:
                    try:
                        bid_js = driver.execute_script("return document.getElementById('bid2') ? document.getElementById('bid2').value : null;")
                        ask_js = driver.execute_script("return document.getElementById('ask2') ? document.getElementById('ask2').value : null;")
                        if bid_js and ask_js:
                            bid = bid_js
                            ask = ask_js
                    except Exception:
                        pass
                now = time.localtime()
                now_str = time.strftime('%Y-%m-%d %H:%M:%S', now)
                sec = now.tm_sec
                # レート取得できた場合のみ記録
                if bid is not None and ask is not None:
                    try:
                        bid_val = float(bid)
                        ask_val = float(ask)
                    except ValueError:
                        print(f"{now_str} レート値変換失敗: Bid={bid} Ask={ask}")
                        time.sleep(0.5)
                        continue
                    print(f"{now_str} Bid: {bid_val} Ask: {ask_val}")
                    # 秒が00なら新しい1分を開始
                    if sec == 0:
                        if bid_list and ask_list:
                            # CSVファイル名が未決定なら、現在時刻を基に作成
                            if csv_file is None:
                                start_ts = time.strftime('%Y%m%d_%H%M%S', time.localtime())
                                csv_file = f"{base_name}_{start_ts}.csv"
                                # ヘッダ追加
                                with open(csv_file, "w", newline="") as hf:
                                    hwriter = csv.writer(hf)
                                    hwriter.writerow([
                                        "datetime", "bid_open", "bid_close", "bid_high", "bid_low",
                                        "ask_open", "ask_close", "ask_high", "ask_low"
                                    ])
                            # 直前の1分間の統計をCSVに記録
                            with open(csv_file, "a", newline="") as f:
                                writer = csv.writer(f)
                                # Bid: 開始値, 終値, 最高値, 最小値
                                bid_open = bid_list[0]
                                bid_close = bid_list[-1]
                                bid_high = max(bid_list)
                                bid_low = min(bid_list)
                                # Ask: 開始値, 終値, 最高値, 最小値
                                ask_open = ask_list[0]
                                ask_close = ask_list[-1]
                                ask_high = max(ask_list)
                                ask_low = min(ask_list)
                                # 日付, 時刻, Bid, Ask
                                # 1分マイナス補正
                                import datetime
                                dt_now = datetime.datetime(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
                                dt_minus1 = dt_now - datetime.timedelta(minutes=1)
                                writer.writerow([
                                    dt_minus1.strftime('%Y-%m-%d %H:%M'),
                                    f"{bid_open:.3f}", f"{bid_close:.3f}", f"{bid_high:.3f}", f"{bid_low:.3f}",
                                    f"{ask_open:.3f}", f"{ask_close:.3f}", f"{ask_high:.3f}", f"{ask_low:.3f}"
                                ])
                            print(f"{now_str} 1分間の統計をCSVに記録しました")
                        # 新しいリストで1分間記録開始
                        bid_list = [bid_val]
                        ask_list = [ask_val]
                        minute_start = now_str
                    else:
                        bid_list.append(bid_val)
                        ask_list.append(ask_val)
                time.sleep(0.5)
            except Exception as e:
                print("レート取得処理で例外:", e)
                time.sleep(1)
    except KeyboardInterrupt:
        print("終了します。ブラウザを閉じます")
        driver.quit()

def order_test(driver):
     # リアルタイム注文のテスト（デフォルト値でテスト）
    print("\n--- リアルタイム注文 速度比較テスト ---")
            
    # 通常版のテスト（execute_order=False）
    print("\n🔄 通常版実行テスト:")
    start_time = time.time()
    operate_realtime_order(driver, "USDJPY", 20000, "sell", execute_order=False)
    normal_time = time.time() - start_time
    print(f"⏱️ 通常版実行時間: {normal_time:.3f}秒")
            
    # 高速版のテスト（execute_order=False）
    print("\n⚡ 高速版実行テスト:")
    start_time = time.time()
    operate_realtime_order_fast(driver, "USDJPY", 20000, "sell", execute_order=False)
    fast_time = time.time() - start_time
    print(f"⏱️ 高速版実行時間: {fast_time:.3f}秒")
            
    # 超高速版のテスト（execute_order=False）
    print("\n🚀 超高速版実行テスト:")
    start_time = time.time()
    operate_realtime_order_ultra_fast(driver, "USDJPY", 20000, "sell", execute_order=False)
    ultra_fast_time = time.time() - start_time
    print(f"⏱️ 超高速版実行時間: {ultra_fast_time:.3f}秒")
            
    # 速度改善の結果表示
    print(f"\n📊 速度改善結果:")
    print(f"   通常版: {normal_time:.3f}秒")
    print(f"   高速版: {fast_time:.3f}秒 ({((normal_time - fast_time) / normal_time * 100):.1f}% 改善)")
    print(f"   超高速版: {ultra_fast_time:.3f}秒 ({((normal_time - ultra_fast_time) / normal_time * 100):.1f}% 改善)")
            


def main():
    global global_driver
    
    # WindowsでのCtrl+C処理はKeyboardInterruptで行います
    print("🔧 Ctrl+C検出の準備完了...")
    print("💡 Ctrl+C: ブラウザ終了とプロセスクリーンアップを実行\n")
    
    login_id = "3006316"
    password = "Sutada53"
    options = webdriver.ChromeOptions()
    
    # ブラウザ実行ファイルは環境変数で上書き可能
    chrome_binary = os.environ.get('CHROME_BINARY')
    if chrome_binary:
        options.binary_location = chrome_binary
    else:
        # Raspberry Pi/Linux の既定場所
        if platform.system() == 'Linux':
            options.binary_location = '/usr/bin/chromium-browser'
        # Windows は通常 binary_location を指定しない（chromedriver が自動でChromeを探す）
    
    # 基本的な安定化オプション
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-extensions')
    options.add_argument('--test-type')  # テストモードフラグ（ChromeDriverプロセス識別用）
    
    # 高度な安定化オプション
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-ipc-flooding-protection')
    
    # ブラウザクラッシュ防止オプション
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-breakpad')  # クラッシュレポート無効
    options.add_argument('--disable-component-extensions-with-background-pages')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-desktop-notifications')
    options.add_argument('--disable-domain-reliability')
    
    # メモリとパフォーマンス最適化
    options.add_argument('--memory-pressure-off')
    options.add_argument('--max_old_space_size=4096')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-plugins-discovery')
    
    # ネットワーク関連の安定化
    options.add_argument('--disable-logging')
    options.add_argument('--disable-login-animations')
    options.add_argument('--disable-password-generation')
    options.add_argument('--disable-save-password-bubble')
    options.add_argument('--disable-session-crashed-bubble')
    options.add_argument('--disable-software-rasterizer')
    
    # 自動化検出回避
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-automation')
    options.add_argument('--disable-infobars')
    
    # 日本語入力対応と安定化設定
    prefs = {
        "profile.default_content_setting_values.notifications": 2,  # 通知無効
        "profile.default_content_settings.popups": 0,  # ポップアップ無効
        "profile.managed_default_content_settings.images": 1,  # 画像読み込み有効（安定性優先）
        "profile.default_content_setting_values.geolocation": 2,  # 位置情報無効
        "profile.default_content_setting_values.media_stream": 2,  # メディア無効
        "profile.password_manager_enabled": False,  # パスワード保存無効
        "credentials_enable_service": False,  # 認証情報サービス無効
        "profile.password_manager_leak_detection": False,  # パスワード漏洩検出無効
    }
    options.add_experimental_option("prefs", prefs)
    
    # 一時プロファイル用のディレクトリを作成（安定性向上）
    import tempfile
    temp_profile_dir = os.path.join(tempfile.gettempdir(), 'chrome_automation_profile_stable')
    # 既存のプロファイルディレクトリをクリア
    try:
        import shutil
        if os.path.exists(temp_profile_dir):
            shutil.rmtree(temp_profile_dir)
            print("🧹 既存のChromeプロファイルをクリアしました")
    except Exception as e:
        print(f"⚠️  プロファイルクリアエラー: {e}")
    
    options.add_argument(f'--user-data-dir={temp_profile_dir}')
    
    print("🔧 高安定性Chromeオプションを設定しました")
    # ChromeDriverの設定（安定性を優先）
    service = None
    chromedriver_path = None
    
    # 1. 環境変数で指定されたパスを最初にチェック
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
    
    # 2. 既存のwebdriver-manager キャッシュをチェック
    if not chromedriver_path:
        try:
            import glob
            # webdriver-manager が通常使用するキャッシュ場所をチェック
            wdm_cache_pattern = os.path.expanduser("~/.wdm/drivers/chromedriver/*/chromedriver*")
            cached_paths = glob.glob(wdm_cache_pattern)
            
            if cached_paths:
                # 最新のキャッシュされたファイルを使用
                chromedriver_path = max(cached_paths, key=os.path.getmtime)
                print(f"Using cached ChromeDriver: {chromedriver_path}")
            
        except Exception as e:
            print(f"Cache check error: {e}")
    
    # 3. webdriver-manager を試行（タイムアウト付き）
    if not chromedriver_path:
        # ARM (Raspberry Pi) の場合、webdriver-manager が x86_64 用バイナリを取得して
        # 実行時に Exec format error となることがあるため、自動取得は行わない。
        arch = platform.machine().lower() if platform.machine() else ''
        is_arm = any(a in arch for a in ('arm', 'aarch'))
        if is_arm:
            print("ARM アーキテクチャが検出されました。webdriver-manager による自動取得をスキップします。")
            print("Raspberry Pi では以下いずれかの対応を行ってください:")
            print(" 1) apt 経由で Chromium と chromedriver をインストール: sudo apt update && sudo apt install -y chromium-browser chromium-chromedriver")
            print(" 2) OS 用にビルド済みの chromedriver (linux-arm / linux-arm64) を入手し、環境変数 CHROMEDRIVER_PATH を設定")
            print(" 3) 既にシステムにある /usr/bin/chromedriver 等のパスを CHROMEDRIVER_PATH に設定")
            chromedriver_path = None
        else:
            try:
                def timeout_handler(signum, frame):
                    raise TimeoutError("ChromeDriverManager timeout")
                # Windowsの場合はタイムアウト処理をスキップ（signalがサポートされていない）
                if platform.system() != 'Windows':
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(30)  # 30秒タイムアウト

                print("ChromeDriverManager を試行中...")
                chromedriver_path = ChromeDriverManager().install()
                print(f"ChromeDriver path: {chromedriver_path}")

                if platform.system() != 'Windows':
                    signal.alarm(0)  # タイマーをリセット

            except (Exception, TimeoutError) as e:
                print(f"ChromeDriverManager failed: {e}")
                chromedriver_path = None
    
    # 4. フォールバック: システムデフォルトパス
    if not chromedriver_path:
        if platform.system() == 'Windows':
            # Windowsの一般的なパス
            potential_paths = [
                r'C:\chromedriver\chromedriver.exe',
                r'C:\Program Files\ChromeDriver\chromedriver.exe',
                r'C:\Windows\System32\chromedriver.exe'
            ]
        else:
            # Linux/Macの一般的なパス
            potential_paths = [
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver',
                '/opt/chromedriver'
            ]
        
        for path in potential_paths:
            if os.path.exists(path):
                chromedriver_path = path
                print(f"Using system ChromeDriver: {chromedriver_path}")
                break
    
    # 5. サービス作成
    if chromedriver_path and os.path.exists(chromedriver_path):
        service = Service(chromedriver_path)
    else:
        # 最終手段: Seleniumにシステムパスから自動検出させる
        print("ChromeDriver path not found, letting Selenium auto-detect...")
        service = Service()
    
    # Chrome起動前のクリーンアップ
    print("=== 起動前クリーンアップを実行 ===")
    try:
        print("既存のChromeDriverプロセスをクリーンアップ中...")
        force_kill_chrome_processes()
        time.sleep(2)  # プロセス終了を確実に待つ
        print("✅ 起動前クリーンアップ完了")
    except Exception as cleanup_e:
        print(f"⚠️ 起動前クリーンアップでエラー: {cleanup_e}")
    
    # Chrome起動（リトライ機能付き）
    print("=== 高安定性Chromeブラウザを起動 ===")
    driver = None
    max_retries = 3
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🚀 ブラウザ起動試行 {attempt}/{max_retries}")
            
            # ブラウザ起動
            driver = webdriver.Chrome(service=service, options=options)
            
            # 起動直後の安定化処理
            time.sleep(2)
            
            # ブラウザの健全性チェック
            print("🔍 ブラウザ健全性チェック中...")
            
            # 基本的な動作確認
            driver.execute_script("return navigator.userAgent;")
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # ウィンドウサイズ確認・調整
            current_size = driver.get_window_size()
            if current_size['width'] != 1920 or current_size['height'] != 1080:
                driver.set_window_size(1920, 1080)
                time.sleep(1)
            
            # タイムアウト設定（安定性向上）
            driver.implicitly_wait(10)  # 要素検索タイムアウト
            driver.set_page_load_timeout(30)  # ページ読み込みタイムアウト
            driver.set_script_timeout(30)  # スクリプト実行タイムアウト
            
            print("✅ Chromeブラウザの起動に成功しました")
            print(f"   ウィンドウサイズ: {driver.get_window_size()}")
            print(f"   UserAgent: {driver.execute_script('return navigator.userAgent;')[:100]}...")
            break
            
        except Exception as e:
            print(f"❌ Chrome起動エラー (試行{attempt}): {e}")
            
            # ドライバーが部分的に起動している場合は終了
            try:
                if driver:
                    driver.quit()
                    driver = None
            except:
                pass
            
            if attempt < max_retries:
                print(f"🔄 {3}秒後に再試行します...")
                
                # プロセスクリーンアップして再試行
                try:
                    kill_chrome()
                    time.sleep(3)
                except:
                    pass
                    
            else:
                print("❌ 全ての起動試行が失敗しました")
                print("🛠️  手動でChromeを終了してから再実行してください")
                return
    
    if not driver:
        print("❌ ブラウザ起動に完全に失敗しました")
        return
    
    # グローバル変数に設定（終了処理用）
    global_driver = driver
    
    # ブラウザ健全性監視機能
    def check_browser_health(driver, operation_name="操作"):
        """ブラウザの健全性をチェックし、問題があれば報告"""
        try:
            # 基本的な接続確認
            current_url = driver.current_url
            
            # JavaScriptの実行確認
            result = driver.execute_script("return 'browser_healthy';")
            
            if result == 'browser_healthy':
                print(f"✅ {operation_name}: ブラウザ健全性OK")
                return True
            else:
                print(f"⚠️  {operation_name}: JavaScript実行異常")
                return False
                
        except Exception as e:
            print(f"❌ {operation_name}: ブラウザ健全性エラー - {e}")
            return False
    
    try:
        # 初期健全性チェック
        if not check_browser_health(driver, "起動後"):
            print("⚠️  ブラウザの初期状態に問題があります")
        
        login_gaikaex(driver, login_id, password)
        # ログイン後の処理
        print('ログイン完了。')
        
        # ログイン後の健全性チェック
        if not check_browser_health(driver, "ログイン後"):
            print("⚠️  ログイン後にブラウザの状態に問題があります")
        
        #print("「新規注文」- 「リアルタイム」を開いたときに表示される、「確認」ダイアログを手動で閉じたら、Enterを押してください。")
        #input("Enterキーを押して続行...")   

        # ページ情報を表示（デバッグ用）
        get_page_source_info(driver)
        
        # 新規注文画面に移動
        print("🔄 新規注文画面への移動を開始...")
        if navigate_to_new_order(driver):
            print("✅ 新規注文画面への移動が成功しました")
            
            # 画面遷移後の健全性チェック
            time.sleep(2)  # 画面描画を待つ
            if not check_browser_health(driver, "画面遷移後"):
                print("⚠️  画面遷移後にブラウザの状態に問題があります")
            
            # 少し待ってから新規注文画面の状況を確認
            time.sleep(1)
            
            # 新規注文画面のフレーム情報を詳細表示
            get_order_frame_info(driver)
            
            # 各注文タイプの操作関数をデモンストレーション
            print("\n=== リアルタイム注文画面の要素分析 ===")
            
            # リアルタイム注文画面の要素を詳細分析
            analyze_form_elements(driver, "realtime")
            
            #print("\n=== リアルタイム注文操作のテスト ===") 
            #order_test()

            print("\n--- 実際の注文実行（高速版使用、execute_order=True）---")

            # Realtime注文の実行（超高速)
            # operate_realtime_order_fast(driver, "USDJPY", 20000, "sell", execute_order=True)  # 高速版を使用
            
            # IFO注文の実行例 
            operate_ifo_order(driver, "USDJPY", 10000, "buy", "limit", 151.50, 153.00, 149.00)
    
            try:
                # main_v2_dフレームに切り替えて内容確認
                driver.switch_to.default_content()
                main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
                driver.switch_to.frame(main_frame)
                
                print(f"最終確認 - ページタイトル: {driver.title}")
                print("新規注文画面が表示されています。確認ダイアログが出た場合は手動で処理してください。")
                
                # ページソースをチェックして確認ダイアログの有無を確認
                page_source = driver.page_source
                if "次回" in page_source and ("表示しない" in page_source or "チェック" in page_source):
                    print("⚠️  確認ダイアログが表示されている可能性があります")
                    print("    - 「次回からこの情報を表示しない」にチェックを入れてください")
                    print("    - 「OK」ボタンをクリックしてください")
                
            except Exception as e:
                print(f"最終確認でエラー: {e}")
            
        else:
            print("❌ 新規注文画面への移動に失敗しました")
        
        # ブラウザを開いたまま待機（定期的な健全性チェック付き）
        print('\nブラウザを開いたまま待機します。終了するには Ctrl+C を押してください。')
        health_check_counter = 0
        while True:
            try:
                time.sleep(1)
                health_check_counter += 1
                
                # 30秒ごとに健全性チェック
                if health_check_counter >= 30:
                    if not check_browser_health(driver, "定期チェック"):
                        print("⚠️  定期チェックでブラウザの異常を検出しました")
                        print("    ブラウザの状態を確認してください")
                    health_check_counter = 0
                    
            except KeyboardInterrupt:
                print('\n🛑 待機中にCtrl+Cが検出されました')
                print('ブラウザ終了処理を実行します...')
                
                # 強化されたブラウザ終了処理
                try:
                    if global_driver:
                        global_driver.quit()
                        print('✅ グローバルドライバーを終了')
                except:
                    pass
                
                try:
                    if 'driver' in locals() and driver:
                        driver.quit()
                        print('✅ ローカルドライバーを終了')
                except:
                    pass
                
                try:
                    force_kill_chrome_processes()
                    print('✅ プロセス強制終了完了')
                except:
                    pass
                
                try:
                    cleanup_remaining_processes()
                    print('✅ 残存プロセスクリーンアップ完了')
                except:
                    pass
                
                print('🏁 待機ループ終了処理完了')
                break
                
    except KeyboardInterrupt:
        print('\n=== 🛑 Ctrl+C が検出されました ===')
        print('ChromeDriverブラウザ終了処理を開始します...')
        
        # 段階1: ブラウザを即座に閉じる
        try:
            if global_driver:
                print("段階1: グローバルドライバーを終了中...")
                global_driver.quit()
                print('✅ グローバルドライバーを終了しました')
        except Exception as e:
            print(f"⚠️  グローバルドライバー終了エラー: {e}")
        
        try:
            if 'driver' in locals() and driver:
                print("段階1: ローカルドライバーを終了中...")
                driver.quit()
                print('✅ ローカルドライバーを終了しました')
        except Exception as e:
            print(f"⚠️  ローカルドライバー終了エラー: {e}")
        
        # 段階2: ChromeDriverプロセス強制終了
        try:
            print("段階2: ChromeDriverプロセス強制終了中...")
            force_kill_chrome_processes()
            print('✅ ChromeDriverプロセス強制終了完了')
        except Exception as e:
            print(f"⚠️  プロセス強制終了エラー: {e}")
        
        # 段階3: 残存プロセス追加クリーンアップ
        try:
            print("段階3: 残存プロセス追加クリーンアップ中...")
            cleanup_remaining_processes()
            print('✅ 残存プロセス追加クリーンアップ完了')
        except Exception as e:
            print(f"⚠️  追加クリーンアップエラー: {e}")
        
        # 段階4: 最終確認
        try:
            print("段階4: 最終プロセス確認中...")
            check_remaining_processes()
        except Exception as e:
            print(f"⚠️  最終確認エラー: {e}")
        
        print("🏁 Ctrl+Cによるブラウザ終了処理が完了しました")
        print("💡 プログラムを完全終了します")
    except Exception as e:
        print(f"❌ エラー: {e}")
        print('例外発生時もブラウザを開いたままにします。終了するには Ctrl+C を押してください。')
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                print('\n=== 🛑 最終KeyboardInterrupt検出 ===')
                print('強制的にブラウザを閉じて終了します...')
                
                # 完全なクリーンアップ処理
                try:
                    if global_driver:
                        global_driver.quit()
                        print('✅ グローバルドライバー強制終了')
                except:
                    pass
                
                try:
                    if 'driver' in locals() and driver:
                        driver.quit()
                        print('✅ ローカルドライバー強制終了')
                except:
                    pass
                
                try:
                    force_kill_chrome_processes()
                    print('✅ 全Chromeプロセス強制終了')
                except:
                    pass
                
                try:
                    cleanup_remaining_processes()
                    print('✅ 残存プロセス完全クリーンアップ')
                except:
                    pass
                
                print('🏁 最終強制終了処理完了')
                break
    finally:
        # 確実にブラウザを閉じる（複数段階の終了処理）
        print("\n=== ブラウザ終了処理を開始 ===")
        
        # 段階1: 通常の終了処理
        try:
            if 'driver' in locals() and driver:
                print("段階1: 通常の終了処理を実行中...")
                driver.quit()
                print("✅ ブラウザが正常に閉じられました。")
            else:
                print("⚠️ ドライバーが初期化されていません")
        except Exception as e:
            print(f"❌ 通常の終了処理でエラー: {e}")
        
        # 段階2: グローバルドライバーの終了処理
        try:
            if global_driver:
                print("段階2: グローバルドライバーの終了処理を実行中...")
                global_driver.quit()
                print("✅ グローバルドライバーが正常に閉じられました。")
        except Exception as e:
            print(f"❌ グローバルドライバー終了でエラー: {e}")
        
        # 段階3: 強制終了処理
        try:
            print("段階3: ChromeDriverプロセスの強制終了を実行中...")
            force_kill_chrome_processes()
            print("✅ ChromeDriverプロセスの強制終了が完了しました。")
        except Exception as force_e:
            print(f"❌ 強制終了処理でもエラー: {force_e}")
        
        # 段階4: 最終クリーンアップ
        try:
            print("段階4: 最終クリーンアップを実行中...")
            kill_chrome()
            print("✅ 最終クリーンアップが完了しました。")
        except Exception as cleanup_e:
            print(f"❌ 最終クリーンアップでエラー: {cleanup_e}")
        
        # 段階5: 追加の残存プロセス確認・終了処理
        try:
            print("段階5: 残存プロセスの確認と終了を実行中...")
            cleanup_remaining_processes()
            print("✅ 残存プロセスの終了が完了しました。")
        except Exception as remaining_e:
            print(f"❌ 残存プロセス終了でエラー: {remaining_e}")
        
        # 段階6: 最終プロセス確認
        try:
            print("段階6: 最終プロセス確認を実行中...")
            check_remaining_processes()
        except Exception as check_e:
            print(f"❌ プロセス確認でエラー: {check_e}")
        
        # グローバル変数をクリア
        global_driver = None
        
        print("=== ブラウザ終了処理完了 ===")
        print("プログラムを終了します。")

def cleanup_remaining_processes():
    """残存するChromeプロセスを強制的に終了する"""
    import psutil
    import subprocess
    import time
    
    terminated_count = 0
    
    try:
        print("🔍 残存するChromeプロセスを検索中...")
        
        # ChromeDriverとChrome関連プロセスを検索
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and proc.info['cmdline']:
                    name_lower = proc.info['name'].lower()
                    cmdline_str = ' '.join(proc.info['cmdline']).lower()
                    
                    # ChromeDriverプロセス
                    if 'chromedriver' in name_lower:
                        print(f"  🎯 ChromeDriver発見: PID {proc.info['pid']}")
                        proc.terminate()
                        terminated_count += 1
                        
                    # 自動化用Chromeプロセス（--test-type等の引数を持つ）
                    elif 'chrome' in name_lower and any(flag in cmdline_str for flag in [
                        '--test-type', '--disable-dev-shm-usage', '--no-sandbox', 
                        '--disable-gpu', '--disable-extensions'
                    ]):
                        print(f"  🎯 自動化Chrome発見: PID {proc.info['pid']}")
                        proc.terminate()
                        terminated_count += 1
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if terminated_count > 0:
            print(f"✅ {terminated_count}個のプロセスを終了しました")
            time.sleep(2)  # プロセス終了を待つ
            
            # 強制終了が必要なプロセスをkillで処理
            print("🔧 強制終了処理を実行中...")
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and proc.info['cmdline']:
                        name_lower = proc.info['name'].lower()
                        cmdline_str = ' '.join(proc.info['cmdline']).lower()
                        
                        if ('chromedriver' in name_lower or 
                            ('chrome' in name_lower and any(flag in cmdline_str for flag in [
                                '--test-type', '--disable-dev-shm-usage'
                            ]))):
                            print(f"  💀 強制終了: PID {proc.info['pid']}")
                            proc.kill()
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        else:
            print("ℹ️  終了対象の残存プロセスは見つかりませんでした")
            
    except Exception as e:
        print(f"⚠️  残存プロセス終了でエラー: {e}")

def check_remaining_processes():
    """残存するChromeプロセスがあるかチェックして報告"""
    import psutil
    
    remaining_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and proc.info['cmdline']:
                    name_lower = proc.info['name'].lower()
                    cmdline_str = ' '.join(proc.info['cmdline']).lower()
                    
                    if ('chromedriver' in name_lower or 
                        ('chrome' in name_lower and any(flag in cmdline_str for flag in [
                            '--test-type', '--disable-dev-shm-usage', '--no-sandbox'
                        ]))):
                        remaining_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': ' '.join(proc.info['cmdline'])[:100] + '...'
                        })
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if remaining_processes:
            print(f"⚠️  {len(remaining_processes)}個の関連プロセスが残存しています:")
            for proc in remaining_processes:
                print(f"     PID {proc['pid']}: {proc['name']}")
                print(f"     コマンド: {proc['cmdline']}")
            print("💡 手動でタスクマネージャーから終了することをお勧めします")
        else:
            print("✅ Chrome関連の残存プロセスはありません")
            
    except Exception as e:
        print(f"⚠️  プロセス確認でエラー: {e}")

if __name__ == "__main__":
    main()
