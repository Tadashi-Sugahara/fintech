# 外貨EXにChromeDriverでログインして、為替レートを取得・自動発注するサンプルコード

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
# プロセス管理機能は使用しない
# from kill_process import force_kill_chrome_processes
# from kill_process import kill_chrome  
# from kill_process import cleanup_remaining_processes

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
    navigate_to_order_correction,
    get_order_correction_info,
    quick_navigate_to_order_correction
)

from monitoring_rates import monitor_usdjpy_rate

import time
import os
import platform
import signal
import atexit
import sys


# グローバルドライバー変数（終了処理用）
global global_driver
global driver
driver = None
global_driver = None

def cleanup_on_exit():
    """プログラム終了時の処理"""
    pass

# プログラム終了時の自動クリーンアップを登録（何もしない）
atexit.register(cleanup_on_exit)
def open_browser():
    global driver
    options = webdriver.ChromeOptions()
    print("Chormeを起動します。")
        
    # Ctrl+Cでプログラム終了
    print("📈 FXトレーディングシステムを開始します")
    print("💡 Ctrl+C でプログラムを終了できます\n")

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
    
    # ブラウザクラッシュ防止オプション（強化版）
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-breakpad')  # クラッシュレポート無効
    options.add_argument('--disable-component-extensions-with-background-pages')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-desktop-notifications')
    options.add_argument('--disable-domain-reliability')
    
    # 強制終了防止のための追加オプション
    options.add_argument('--disable-hang-monitor')  # ハングモニター無効化
    options.add_argument('--disable-prompt-on-repost')  # 再送信プロンプト無効化
    options.add_argument('--disable-client-side-phishing-detection')  # フィッシング検出無効化
    options.add_argument('--disable-component-update')  # コンポーネント更新無効化
    options.add_argument('--disable-background-mode')  # バックグラウンドモード無効化
    options.add_argument('--disable-features=TranslateUI')  # 翻訳UI無効化
    options.add_argument('--disable-features=VizDisplayCompositor,VizServiceDisplay')  # 描画処理最適化
    options.add_argument('--force-device-scale-factor=1')  # DPI固定
    
    # メモリとパフォーマンス最適化（強化版）
    options.add_argument('--memory-pressure-off')
    options.add_argument('--max_old_space_size=4096')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-plugins-discovery')
    
    # リソース制限とメモリ管理
    options.add_argument('--max-tiles-for-interest-area=512')  # タイル数制限
    options.add_argument('--num-raster-threads=4')  # ラスタースレッド数制限
    options.add_argument('--enable-tcp-fast-open')  # TCP高速化
    options.add_argument('--disable-partial-raster')  # 部分ラスター無効化
    
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
    
    # プロセスクリーンアップは実行しない
    print("=== Chromeブラウザを起動します ===")
    
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
                time.sleep(3)
                    
            else:
                print("❌ 全ての起動試行が失敗しました")
                print("🛠️  手動でChromeを終了してから再実行してください")
                return
    
    if not driver:
        print("❌ ブラウザ起動に完全に失敗しました")
        return None
    
    # グローバル変数に設定（終了処理用）
    global global_driver
    global_driver = driver
    return driver


def main():
    global driver
 
    login_id = "3006316"
    password = "Sutada53"

    driver = open_browser()
    
    if not driver:
        print("❌ ブラウザの起動に失敗しました")
        return

    try:
        login_gaikaex(driver, login_id, password)
        # ログイン後の処理
        print('✅ ログイン完了。')
    
        # ページ情報を表示（デバッグ用）
        get_page_source_info(driver)
        
        if navigate_to_new_order(driver):
            # print("✅ 新規注文画面への移動が成功しました")
            
            # 画面遷移後の安定化処理
            time.sleep(2)  # 画面描画を十分に待つ（安定性向上）

            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                #print("✅ 画面読み込みが完了しました")
            except TimeoutException:
                print("⚠️  画面読み込みがタイムアウトしましたが、処理を続行します")
            
            print("初期メッセージの確認をチェックしてください。")
            input("Enterキーを押して続行...")

            # Realtime注文の実行（超高速)
            # operate_realtime_order_fast(driver, "USDJPY", 20000, "sell", execute_order=True)  # 高速版を使用
            
            # IFO注文の実行例 
            #operate_ifo_order(driver, "USDJPY", 10000, "buy", "limit", 151.50, 153.00, 149.00)
            
            #注文訂正画面への移動と情報取得のテスト
            quick_navigate_to_order_correction(driver)
   

        else:
            print("❌ 新規注文画面への移動に失敗しました")
        
        # シンプルな待機ループ（Ctrl+Cで終了）
        print('\nプログラムを終了するには Ctrl+C を押してください。')
        
        try:
            while True:
                time.sleep(1)
                # ここに他の定期処理を追加可能


        except KeyboardInterrupt:
            print('\n🛑 Ctrl+Cが検出されました')
            print('🏁 プログラムを終了します')
                
    except KeyboardInterrupt:
        print('\n🛑 プログラムを終了します')
    except Exception as e:
        print(f"❌ エラー: {e}")
        print('🏁 プログラムを終了します')
    finally:
        # ブラウザを閉じる
        try:
            if driver:
                driver.quit()
                print("✅ ブラウザを正常に終了しました")
        except Exception as e:
            print(f"⚠️  ブラウザ終了エラー: {e}")
        
        # グローバル変数をクリア
        driver = None
        global global_driver
        global_driver = None
        print("🏁 プログラム終了")

if __name__ == "__main__":
    main()
