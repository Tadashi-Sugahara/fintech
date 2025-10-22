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

# グローバルドライバー変数（終了処理用）
global_driver = None


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

def order_test():
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
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-extensions')  # 拡張機能を無効にする
    options.add_argument('--test-type')  # テストモードフラグ（ChromeDriverプロセス識別用）
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-features=VizDisplayCompositor')  # 描画安定化
    options.add_argument('--disable-ipc-flooding-protection')  # IPC制限解除
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 日本語入力対応と安定化設定
    prefs = {
        "profile.default_content_setting_values.notifications": 2,  # 通知無効
        "profile.default_content_settings.popups": 0,  # ポップアップ無効
        "profile.managed_default_content_settings.images": 2  # 画像読み込み無効（高速化）
    }
    options.add_experimental_option("prefs", prefs)
    
    # 一時プロファイル用のディレクトリを作成
    import tempfile
    temp_profile_dir = os.path.join(tempfile.gettempdir(), 'chrome_automation_profile')
    options.add_argument(f'--user-data-dir={temp_profile_dir}')
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
                import signal
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
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        # ユーザーエージェントを設定（自動化検出を回避）
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception as e:
        print(f"Chrome起動エラー: {e}")
        print("代替方法として、既存のChromeプロセスを終了して再試行します...")
        kill_chrome()
        time.sleep(3)
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e2:
            print(f"再試行も失敗: {e2}")
            print("手動でChromeを終了してから再実行してください")
            return
    
    # グローバル変数に設定（終了処理用）
    global_driver = driver
    
    try:
        login_gaikaex(driver, login_id, password)
        # ログイン後の処理
        print('ログイン完了。')
        
        #print("「新規注文」- 「リアルタイム」を開いたときに表示される、「確認」ダイアログを手動で閉じたら、Enterを押してください。")
        #input("Enterキーを押して続行...")   

        # ページ情報を表示（デバッグ用）
        get_page_source_info(driver)
        
        # 新規注文画面に移動
        if navigate_to_new_order(driver):
            print("✅ 新規注文画面への移動が成功しました")
            
            # 少し待ってから新規注文画面の状況を確認
            time.sleep(0.1)
            
            # 新規注文画面のフレーム情報を詳細表示
            get_order_frame_info(driver)
            
            # 各注文タイプの操作関数をデモンストレーション
            print("\n=== リアルタイム注文画面の要素分析 ===")
            
            # リアルタイム注文画面の要素を詳細分析
            analyze_form_elements(driver, "realtime")
            
            #print("\n=== リアルタイム注文操作のテスト ===") 
            #order_test()

            print("\n--- 実際の注文実行（高速版使用、execute_order=True）---")
            operate_realtime_order_fast(driver, "USDJPY", 20000, "sell", execute_order=True)  # 高速版を使用
            
    
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
        
        # ブラウザを開いたまま待機
        print('\nブラウザを開いたまま待機します。終了するには Ctrl+C を押してください。')
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                print('\nKeyboardInterrupt を受け取りました。ブラウザを閉じます。')
                break
                
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt を受け取りました。ブラウザを閉じます。')
    except Exception as e:
        print("エラー:", e)
        print('例外発生時もブラウザを開いたままにします。終了するには Ctrl+C を押してください。')
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                print('\nKeyboardInterrupt を受け取りました。ブラウザを閉じます。')
                break
    finally:
        # 確実にブラウザを閉じる
        try:
            print("ブラウザを閉じています...")
            driver.quit()
            print("ブラウザが正常に閉じられました。")
        except Exception as e:
            print(f"通常の終了処理でエラー: {e}")
            # 強制終了処理を実行
            try:
                print("強制終了処理を実行中...")
                force_kill_chrome_processes()
            except Exception as force_e:
                print(f"強制終了処理でもエラー: {force_e}")
        
        # グローバルドライバーもクリア
        global_driver = None
        
        print("プログラムを終了します。")

if __name__ == "__main__":
    main()
