# 外貨EXにChromeDriverでログインして、為替レートを取得するサンプルコード
# 事前にChromeDriverをインストールしておくこと

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import platform
import sys
import signal
import atexit
import subprocess
import psutil

# グローバルドライバー変数（終了処理用）
global_driver = None

def cleanup_driver():
    """プログラム終了時にドライバーをクリーンアップする関数"""
    global global_driver
    if global_driver:
        try:
            print("\n緊急終了: ブラウザを閉じています...")
            
            # 1. 通常の終了処理を試行（短時間制限付き）
            import threading
            import time
            
            def quit_driver():
                try:
                    global_driver.quit()
                except:
                    pass
            
            # 別スレッドで終了処理を実行（デッドロック防止）
            quit_thread = threading.Thread(target=quit_driver)
            quit_thread.daemon = True
            quit_thread.start()
            quit_thread.join(timeout=3)  # 3秒でタイムアウト
            
            if quit_thread.is_alive():
                print("通常終了がタイムアウトしました。強制終了を実行します。")
                force_kill_chrome_processes()
            else:
                print("ブラウザが正常に閉じられました。")
            
        except Exception as e:
            print(f"終了処理でエラー: {e}")
            
            # 2. 強制終了処理を実行
            try:
                print("強制終了処理を実行中...")
                force_kill_chrome_processes()
            except Exception as force_e:
                print(f"強制終了処理でもエラー: {force_e}")
                
    # 最終手段：ChromeDriverプロセスのみ終了
    try:
        if platform.system() == 'Windows':
            subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'], 
                         capture_output=True, timeout=3)
            print("chromedriver.exeのみを最終終了しました")
    except:
        pass

def force_kill_chrome_processes():
    """ChromeDriverで開いたブラウザのみを強制終了（通常のChromeは残す）"""
    try:
        killed_processes = []
        chrome_driver_pids = set()
        
        # まずchromedriver.exeプロセスを見つける
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_name = proc.info['name'].lower() if proc.info['name'] else ''
                
                if 'chromedriver' in proc_name:
                    chrome_driver_pids.add(proc.info['pid'])
                    try:
                        proc.kill()
                        killed_processes.append(f"chromedriver({proc.info['pid']})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # ChromeDriverによって起動されたChromeプロセスのみを特定して終了
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
            try:
                proc_name = proc.info['name'].lower() if proc.info['name'] else ''
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                
                # ChromeDriverで起動されたChromeプロセスの特徴を確認
                if 'chrome.exe' in proc_name and any([
                    '--test-type' in cmdline,           # テストモードフラグ
                    '--disable-extensions' in cmdline,  # 拡張機能無効フラグ  
                    '--disable-dev-shm-usage' in cmdline, # 開発用フラグ
                    '--no-sandbox' in cmdline,          # サンドボックス無効フラグ
                    '--remote-debugging-port' in cmdline, # デバッグポート
                    '--disable-gpu' in cmdline,         # GPU無効フラグ
                    proc.info['ppid'] in chrome_driver_pids  # chromedriver が親プロセス
                ]):
                    try:
                        proc.terminate()  # 通常終了を試行
                        proc.wait(timeout=2)  # 2秒待機
                        killed_processes.append(f"chrome({proc.info['pid']})")
                    except psutil.TimeoutExpired:
                        # 2秒で終了しない場合は強制終了
                        proc.kill()
                        killed_processes.append(f"chrome({proc.info['pid']}) [FORCE]")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if killed_processes:
            print(f"ChromeDriverのプロセスのみ終了: {', '.join(killed_processes)}")
        else:
            print("ChromeDriverプロセスが見つかりませんでした")
            
    except Exception as e:
        print(f"プロセス特定終了でエラー: {e}")
        
        # フォールバック: chromedriver.exeのみ終了
        try:
            if platform.system() == 'Windows':
                subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'], 
                             capture_output=True, timeout=3)
                print("chromedriver.exeのみ終了しました")
            else:
                subprocess.run(['pkill', '-f', 'chromedriver'], 
                             capture_output=True, timeout=3)
                print("chromedriverプロセスのみ終了しました")
        except Exception as cmd_e:
            print(f"chromedriver終了でもエラー: {cmd_e}")

def signal_handler(signum, frame):
    """シグナルハンドラー（Ctrl+C処理）"""
    print(f"\nシグナル {signum} を受信しました。プログラムを強制終了します。")
    
    # まず通常のクリーンアップを試行
    cleanup_driver()
    
    # 少し待ってから強制終了も実行
    try:
        time.sleep(1)
        force_kill_chrome_processes()
    except:
        pass
    
    # 最終手段: chromedriver.exeのみを確実に終了
    try:
        import subprocess
        if platform.system() == 'Windows':
            subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'], 
                         capture_output=True, timeout=5)
            print("chromedriver.exeのみを終了しました。")
    except:
        pass
    
    print("プログラムを終了します。")
    os._exit(0)  # sys.exit()の代わりにより強力な終了を使用

# シグナルハンドラーの登録（Windowsでサポートされているもののみ）
try:
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)  # 終了シグナル
except Exception as e:
    print(f"シグナルハンドラーの登録に失敗: {e}")

# プログラム終了時の自動クリーンアップ
atexit.register(cleanup_driver)

# ログイン処理
def login_gaikaex(driver, login_id, password):
    login_url = "https://vt-fx.gaikaex.com/servlet/login"
    driver.get(login_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginID")))
    driver.find_element(By.ID, "LoginID").send_keys(login_id)
    driver.find_element(By.ID, "Pass").send_keys(password)
    driver.find_element(By.NAME, "loginBtn").click()
    time.sleep(3)
    print("ログイン後タイトル:", driver.title)
    print("ログイン成功。Ctrl+Cで終了します")


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

def navigate_to_new_order(driver):
    """
    外貨exのメイン画面から「新規注文」メニューに移動する関数
    """

    try:
        print("新規注文メニューに移動しています...")
        
        # 1. デフォルトコンテンツに戻る
        driver.switch_to.default_content()
        time.sleep(0.5)
        
        # 2. mainMenuフレームに切り替え
        try:
            main_menu_frame = driver.find_element(By.CSS_SELECTOR, "iframe#mainMenu, iframe[name='mainMenu']")
            driver.switch_to.frame(main_menu_frame)
            #print("mainMenuフレームに切り替えました")
        except Exception as e:
            print(f"mainMenuフレームの切り替えに失敗: {e}")
            return False
        
        # 3. 「取引」メニューが開いているか確認し、必要に応じて開く
        try:
            # h3#1 が「取引」メニューのヘッダー
            trade_menu_header = driver.find_element(By.ID, "1")
            
            # selectedクラスがない場合はクリックしてメニューを開く
            if "selected" not in trade_menu_header.get_attribute("class"):
                print("「取引」メニューを開きます...")
                trade_menu_header.click()
                time.sleep(0.1)
            else:
                print("「取引」メニューは既に開いています")
                
        except Exception as e:
            print(f"「取引」メニューの操作に失敗: {e}")
            return False
        
        # 4. 「新規注文」リンクをクリック
        try:
            # menu01内の「新規注文」リンクを探す
            new_order_link = driver.find_element(By.XPATH, "//ul[@id='menu01']//a[contains(text(), '新規注文')]")
            
            if new_order_link.is_displayed():
                #print("「新規注文」リンクをクリックします...")
                new_order_link.click()
                time.sleep(0.2)  # ページ遷移を待つ
                print("「新規注文」画面への移動が完了しました")
                return True
            else:
                print("「新規注文」リンクが表示されていません")
                return False
                
        except Exception as e:
            print(f"「新規注文」リンクのクリックに失敗: {e}")
            return False
            
    except Exception as e:
        print(f"新規注文メニューへの移動でエラーが発生: {e}")
        return False
    
    finally:
        # デフォルトコンテンツに戻る
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def get_page_source_info(driver):
    """
    現在のページソースとフレーム情報を表示するデバッグ用関数
    """
    try:
        print("\n=== ページ情報の取得 ===")
        
        # メインページのタイトルと基本情報
        driver.switch_to.default_content()
        #print(f"メインページタイトル: {driver.title}")
        #print(f"現在のURL: {driver.current_url}")
        
        # iframeの一覧を取得
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        #print(f"iframe数: {len(iframes)}")
        
        for i, iframe in enumerate(iframes):
            iframe_id = iframe.get_attribute("id") or "no-id"
            iframe_name = iframe.get_attribute("name") or "no-name"
            iframe_src = iframe.get_attribute("src") or "no-src"
            #print(f"  iframe[{i}]: id={iframe_id}, name={iframe_name}, src={iframe_src[:100]}...")
        
        # mainMenuフレーム内の情報を確認
        try:
            main_menu_frame = driver.find_element(By.CSS_SELECTOR, "iframe#mainMenu, iframe[name='mainMenu']")
            driver.switch_to.frame(main_menu_frame)
            
            # メニュー項目を取得
            menu_headers = driver.find_elements(By.TAG_NAME, "h3")
            #print(f"\nメニューヘッダー数: {len(menu_headers)}")
            
            for header in menu_headers:
                header_id = header.get_attribute("id")
                header_text = header.text
                header_class = header.get_attribute("class") or "no-class"
                #print(f"  メニュー[{header_id}]: '{header_text}' (class: {header_class})")
                
                # 対応するメニュー項目を表示
                try:
                    menu_ul = driver.find_element(By.ID, f"menu0{header_id}")
                    menu_items = menu_ul.find_elements(By.TAG_NAME, "a")
                    for item in menu_items:
                        item_text = item.text
                        onclick = item.get_attribute("onclick") or "no-onclick"
                        #print(f"    - {item_text}")
                except Exception:
                    pass
                    
        except Exception as e:
            #print(f"mainMenuフレームの情報取得に失敗: {e}")
            pass
        
        print("")
        print("=========================\n")

        
    except Exception as e:
        print(f"ページ情報の取得でエラーが発生: {e}")
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


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
    options.add_argument('--window-size=1280,800')
    options.add_argument('--disable-extensions')  # 拡張機能を無効にする
    options.add_argument('--test-type')  # テストモードフラグ（ChromeDriverプロセス識別用）
    
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
    driver = webdriver.Chrome(service=service, options=options)
    
    # グローバル変数に設定（終了処理用）
    global_driver = driver
    
    try:
        login_gaikaex(driver, login_id, password)
        # ログイン後の処理
        print('ログイン完了。')
        
        print("「新規注文」- 「リアルタイム」を開いたときに表示される、「確認」ダイアログを手動で閉じたら、Enterを押してください。")
        input("Enterキーを押して続行...")   


        # ページ情報を表示（デバッグ用）
        get_page_source_info(driver)
        
        # 新規注文画面に移動
        if navigate_to_new_order(driver):
            print("✅ 新規注文画面への移動が成功しました")
            
            # 少し待ってから新規注文画面の状況を確認
            time.sleep(3)
            
            try:
                # main_v2_dフレームに切り替えて内容確認
                driver.switch_to.default_content()
                main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
                driver.switch_to.frame(main_frame)
                
                print(f"新規注文画面のタイトル: {driver.title}")
                print("新規注文画面が表示されています。確認ダイアログが出た場合は手動で処理してください。")
                
                # ページソースをチェックして確認ダイアログの有無を確認
                page_source = driver.page_source
                if "次回" in page_source and ("表示しない" in page_source or "チェック" in page_source):
                    print("⚠️  確認ダイアログが表示されている可能性があります")
                    print("    - 「次回からこの情報を表示しない」にチェックを入れてください")
                    print("    - 「OK」ボタンをクリックしてください")
                
            except Exception as e:
                print(f"新規注文画面の確認でエラー: {e}")
            
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
