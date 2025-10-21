# 外貨EXにChromeDriverでログインして、為替レートを取得するサンプルコード
# 事前にChromeDriverをインストールしておくこと

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import platform
import sys
import signal
import atexit
import subprocess
import psutil

##

# グローバルドライバー変数（終了処理用）
global_driver = None

def kill_chrome():
    """Chromeプロセスを強制終了する関数"""
    try:
        if platform.system() == 'Windows':
            # Windowsの場合
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Linux/Macの場合
            subprocess.run(['pkill', '-f', 'chrome'], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-f', 'chromedriver'], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("既存のChromeプロセスを終了しました")
        time.sleep(2)
    except Exception as e:
        print(f"Chrome終了処理でエラー: {e}")

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
    
    # ログインフォームの読み込み完了を待機
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginID")))
    
    # ログインID入力
    login_id_field = driver.find_element(By.ID, "LoginID")
    login_id_field.clear()  # フィールドをクリア
    time.sleep(0.3)
    login_id_field.send_keys(login_id)
    
    # 入力値確認
    entered_login_id = login_id_field.get_attribute("value")
    print(f"入力されたログインID: {entered_login_id}")
    
    # ログインIDが正しく入力されていない場合はJavaScriptで入力
    if entered_login_id != login_id:
        print("⚠️  ログインIDが正しく入力されていません。JavaScriptで再入力します...")
        driver.execute_script("arguments[0].value = arguments[1];", login_id_field, login_id)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", login_id_field)
        entered_login_id = login_id_field.get_attribute("value")
        print(f"JavaScript入力後のログインID: {entered_login_id}")
    
    # パスワード入力
    password_field = driver.find_element(By.ID, "Pass")
    password_field.clear()  # フィールドをクリア
    time.sleep(0.5)  # 少し待機
    
    # 方法1: 通常のsend_keys
    password_field.send_keys(password)
    
    # 入力値確認（デバッグ用）
    entered_password = password_field.get_attribute("value")
    print(f"入力されたパスワード長: {len(entered_password)} 文字")
    
    # パスワードが正しく入力されていない場合は代替方法を使用
    if len(entered_password) != len(password) or entered_password != password:
        print("⚠️  パスワードが正しく入力されていません。JavaScriptで再入力します...")
        
        # 方法2: JavaScriptで直接値を設定
        driver.execute_script("arguments[0].value = '';", password_field)  # クリア
        time.sleep(0.5)
        driver.execute_script("arguments[0].value = arguments[1];", password_field, password)
        
        # 入力イベントを発火
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", password_field)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", password_field)
        
        # 再確認
        entered_password = password_field.get_attribute("value")
        print(f"JavaScript入力後のパスワード長: {len(entered_password)} 文字")
        
        # まだ正しく入力されていない場合は一文字ずつ入力
        if len(entered_password) != len(password):
            print("⚠️  JavaScript入力も失敗しました。一文字ずつ入力します...")
            password_field.clear()
            time.sleep(1)
            for char in password:
                password_field.send_keys(char)
                time.sleep(0.1)
            
            # 最終確認
            entered_password = password_field.get_attribute("value")
            print(f"一文字ずつ入力後のパスワード長: {len(entered_password)} 文字")
    
    # ログインボタンをクリック
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

def navigate_to_order_type(driver, order_type="realtime"):
    """
    新規注文画面の各メニューに移動する関数
    
    Args:
        driver: WebDriverインスタンス
        order_type: 注文タイプ（"realtime", "limit", "ifd", "oco", "ifo"）
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"注文タイプ '{order_type}' に移動しています...")
        
        # main_v2_dフレーム（新規注文画面）に切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 注文タイプとJavaScript関数のマッピング
        order_mappings = {
            "realtime": {
                "servlet": "/servlet/lzca.pc.cht001.servlet.CHt00102",
                "key": "Ht00102",
                "display_name": "リアルタイム"
            },
            "limit": {
                "servlet": "/servlet/lzca.pc.cht001.servlet.CHt00111", 
                "key": "Ht00111",
                "display_name": "指値・逆指値"
            },
            "ifd": {
                "servlet": "/servlet/lzca.pc.cht001.servlet.CHt00121",
                "key": "Ht00121", 
                "display_name": "IFD"
            },
            "oco": {
                "servlet": "/servlet/lzca.pc.cht001.servlet.CHt00131",
                "key": "Ht00131",
                "display_name": "OCO"
            },
            "ifo": {
                "servlet": "/servlet/lzca.pc.cht001.servlet.CHt00141",
                "key": "Ht00141",
                "display_name": "IFO"
            }
        }
        
        if order_type not in order_mappings:
            print(f"❌ 無効な注文タイプ: {order_type}")
            print(f"有効な注文タイプ: {list(order_mappings.keys())}")
            return False
        
        mapping = order_mappings[order_type]
        
        # settlement_naviエリア内のリンクを探す
        try:
            # 対象のリンクを探す（テキストベース）
            target_link = driver.find_element(By.XPATH, 
                f"//div[@class='settlement_navi']//a[contains(text(), '{mapping['display_name']}')]")
            
            if target_link.is_displayed():
                print(f"'{mapping['display_name']}' リンクをクリックします...")
                target_link.click()
                time.sleep(2)  # ページ遷移待機
                
                # 遷移確認
                try:
                    # アクティブなリンクを確認
                    active_link = driver.find_element(By.XPATH, 
                        "//div[@class='settlement_navi']//a[@class='active']")
                    if mapping['display_name'] in active_link.text:
                        print(f"✅ '{mapping['display_name']}' 画面への移動が成功しました")
                        return True
                    else:
                        print(f"⚠️  移動しましたが、期待したページでない可能性があります")
                        return False
                except Exception:
                    print("アクティブリンクの確認ができませんでしたが、クリックは実行されました")
                    return True
            else:
                print(f"'{mapping['display_name']}' リンクが表示されていません")
                return False
                
        except Exception as e:
            print(f"リンク検索でエラー: {e}")
            
            # フォールバック: JavaScript実行による直接遷移
            try:
                print("JavaScriptによる直接遷移を試行...")
                js_command = f"_submitForm('{mapping['servlet']}', '{mapping['key']}');"
                driver.execute_script(js_command)
                time.sleep(2)
                print(f"✅ JavaScript実行で '{mapping['display_name']}' に移動しました")
                return True
            except Exception as js_e:
                print(f"JavaScript実行でもエラー: {js_e}")
                return False
                
    except Exception as e:
        print(f"注文タイプ移動でエラーが発生: {e}")
        return False
    
    finally:
        # フレームを元に戻す（エラー時も実行）
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def get_order_frame_info(driver):
    """
    新規注文画面のフレーム情報を取得・表示する関数
    """
    try:
        #print("\n=== 新規注文画面フレーム情報 ===")
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # ページタイトル確認
        page_title = driver.title
        #print(f"ページタイトル: {page_title}")
        
        # 現在のURL確認
        current_url = driver.current_url
        #print(f"現在のURL: {current_url}")
        
        # settlement_naviメニューの状態確認
        try:
            navi_links = driver.find_elements(By.XPATH, "//div[@class='settlement_navi']//a")
            #print(f"\n注文タイプメニュー ({len(navi_links)}個):")
            
            for i, link in enumerate(navi_links):
                try:
                    link_text = link.text.strip()
                    link_class = link.get_attribute("class") or ""
                    onclick = link.get_attribute("onclick") or ""
                    is_active = "active" in link_class
                    status = "🔴 [ACTIVE]" if is_active else "⚪"
                    
                    #print(f"  {status} {link_text}")
                    if onclick:
                        #print(f"       onclick: {onclick[:80]}...")
                        print("")

                except Exception:
                    print(f"  [リンク{i}] 情報取得エラー")
        except Exception as e:
            print(f"メニュー情報取得エラー: {e}")
        
        # iframeの確認
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            #print(f"\n埋め込みフレーム ({len(iframes)}個):")
            
            for i, iframe in enumerate(iframes):
                try:
                    iframe_id = iframe.get_attribute("id") or "no-id"
                    iframe_name = iframe.get_attribute("name") or "no-name"
                    iframe_src = iframe.get_attribute("src") or "no-src"
                    iframe_class = iframe.get_attribute("class") or "no-class"
                    
                    #print(f"  iframe[{i}]: id={iframe_id}, name={iframe_name}")
                    #print(f"              class={iframe_class}")
                    #print(f"              src={iframe_src[:100]}...")
                    
                except Exception:
                    print(f"  iframe[{i}]: 情報取得エラー")
                    
        except Exception as e:
            print(f"iframe情報取得エラー: {e}")
        
        # フォーム情報の確認
        try:
            forms = driver.find_elements(By.TAG_NAME, "form")
           # print(f"\nフォーム情報 ({len(forms)}個):")
            
            for i, form in enumerate(forms):
                try:
                    form_name = form.get_attribute("name") or "no-name"
                    hidden_inputs = form.find_elements(By.XPATH, ".//input[@type='hidden']")
                    
                    #print(f"  form[{i}]: name={form_name}")
                    #print(f"            hidden inputs: {len(hidden_inputs)}個")
                    
                    # 重要なhidden inputを表示
                    for hidden in hidden_inputs[:5]:  # 最初の5個だけ
                        input_name = hidden.get_attribute("name") or "no-name"
                        input_value = hidden.get_attribute("value") or "no-value"
                        #print(f"              {input_name}={input_value}")
                        
                except Exception:
                    print(f"  form[{i}]: 情報取得エラー")
                    
        except Exception as e:
            print(f"フォーム情報取得エラー: {e}")
        
        #print("===============================\n")
        
    except Exception as e:
        print(f"フレーム情報取得でエラーが発生: {e}")
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


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


def quick_navigate_to_order(driver, order_type="realtime"):
    """
    新規注文画面に移動して、指定された注文タイプを開く便利関数
    
    Args:
        driver: WebDriverインスタンス
        order_type: 注文タイプ（"realtime", "limit", "ifd", "oco", "ifo"）
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"新規注文 - {order_type.upper()} への直接移動を開始...")
        
        # 1. 新規注文画面に移動
        if not navigate_to_new_order(driver):
            print("❌ 新規注文画面への移動に失敗")
            return False
        
        time.sleep(2)
        
        # 2. 指定された注文タイプに移動
        if not navigate_to_order_type(driver, order_type):
            print(f"❌ {order_type} 画面への移動に失敗")
            return False
        
        print(f"✅ 新規注文 - {order_type.upper()} への移動が完了しました")
        return True
        
    except Exception as e:
        print(f"quick_navigate_to_order でエラー: {e}")
        return False


def display_available_order_types():
    """
    利用可能な注文タイプを表示する関数
    """
    print("\n=== 利用可能な注文タイプ ===")
    order_types = {
        "realtime": "リアルタイム注文",
        "limit": "指値・逆指値注文", 
        "ifd": "IFD注文（If Done）",
        "oco": "OCO注文（One Cancels Other）",
        "ifo": "IFO注文（If Done + OCO）"
    }
    
    for key, description in order_types.items():
        print(f"  {key:<10} : {description}")
    
    print("\n使用例:")
    print("  navigate_to_order_type(driver, 'limit')     # 指値・逆指値に移動")
    print("  quick_navigate_to_order(driver, 'ifd')      # 新規注文→IFDに直接移動")
    print("=============================\n")


# ===== 各注文タイプ専用の操作関数 =====

def operate_realtime_order(driver, pair, amount, order_type, execute_order, silent=False):
    """
    リアルタイム注文を実行する関数（高速化版）
    
    Args:
        driver: WebDriverインスタンス
        pair: 通貨ペア（例: "USDJPY"）
        amount: 注文数量（例: 10000）
        order_type: 注文種別（"buy"または"sell"）
        execute_order: 実際に注文を実行するかどうか
        silent: メッセージ表示を最小限に抑える（高速化）
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        #print(f"リアルタイム注文画面を操作します（{pair}, {amount}, {order_type}）...")
        #print(f"🔍 引数確認: execute_order={execute_order} (型: {type(execute_order)})")
        
        # リアルタイム注文画面に移動
        if not navigate_to_order_type(driver, "realtime"):
            print("❌ リアルタイム注文画面への移動に失敗")
            return False
        
        # main_v2_dフレームに切り替え
        try:
            driver.switch_to.default_content()
            main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
            driver.switch_to.frame(main_frame)
            #print("✅ main_v2_dフレームに切り替えました")
            
            # さらに内側のフレームがあるかチェック
            time.sleep(0.1)  # フレーム読み込み待機
            
            # フレーム内のiframe要素を探す
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            #print(f"📋 フレーム内のiframe数: {len(iframes)}")
            
            # 注文フォームが含まれるiframeを探す
            form_found = False
            for i, iframe in enumerate(iframes):
                try:
                    # 各iframeに切り替えて確認
                    driver.switch_to.frame(iframe)
                    #print(f"📍 iframe[{i}]に切り替えました")
                    
                    # 注文フォーム要素があるかチェック
                    try:
                        # 通貨ペア選択またはボタンがあるかチェック
                        selects = driver.find_elements(By.TAG_NAME, "select")
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        visible_inputs = driver.find_elements(By.XPATH, "//input[@type='text' and not(contains(@style, 'display:none') or contains(@style, 'display: none') or contains(@class, 'displayNone'))]")
                        
                        #print(f"    選択欄: {len(selects)}個, ボタン: {len(buttons)}個, 表示テキスト入力: {len(visible_inputs)}個")
                        
                        # 注文フォーム要素が見つかった場合
                        if len(selects) > 0 or len(buttons) > 0 or len(visible_inputs) > 0:
                            #print(f"✅ 注文フォームが見つかりました（iframe[{i}]）")
                            form_found = True
                            break
                            
                    except Exception:
                        pass
                    
                    # 注文フォームが見つからない場合は元のフレームに戻る
                    driver.switch_to.default_content()
                    driver.switch_to.frame(main_frame)
                    
                except Exception as e:
                    print(f"iframe[{i}]の切り替えでエラー: {e}")
                    # エラーの場合は元のフレームに戻る
                    driver.switch_to.default_content()
                    driver.switch_to.frame(main_frame)
                    continue
            
            if not form_found and len(iframes) == 0:
                print("📝 内側のiframeは見つかりませんでした。メインフレームで処理を続行します。")
            
        except Exception as frame_e:
            print(f"❌ フレーム切り替えでエラー: {frame_e}")
            # フレーム一覧を表示
            try:
                driver.switch_to.default_content()
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                print(f"現在のiframe数: {len(iframes)}")
                for i, iframe in enumerate(iframes):
                    iframe_id = iframe.get_attribute("id") or "no-id"
                    iframe_name = iframe.get_attribute("name") or "no-name"
                    print(f"  iframe[{i}]: id={iframe_id}, name={iframe_name}")
            except Exception:
                pass
            return False
        
        # 確認ダイアログが表示されているかチェック
        try:
            disclaimer_modal = driver.find_element(By.ID, "disclaimer-modal-content_entry")
            disclaimer_style = disclaimer_modal.get_attribute("class")
            
            if "displayNone" not in disclaimer_style:
                print("⚠️  確認ダイアログが表示されています")
                print("    手動でダイアログを処理してください:")
                print("    1. 「次回からこの確認を表示しない」にチェック（推奨）")
                print("    2. 「OK」ボタンをクリック")
                print("    3. 処理が完了したら、このスクリプトを再実行してください")
                return False
        except Exception:
            # ダイアログが見つからない場合は処理続行
            print("📝 確認ダイアログは表示されていません")
        
        # 注文フォームが表示されているかチェック
        try:
            entry_div = driver.find_element(By.ID, "entry")
            entry_style = entry_div.get_attribute("class")
            
            if "displayNone" in entry_style:
                print("⚠️  注文フォームがまだ表示されていません")
                print("    確認ダイアログの処理が必要な可能性があります")
                
                # JavaScriptでダイアログを強制的に閉じる試行
                try:
                    print("🔧 JavaScriptで注文フォームの表示を試行...")
                    driver.execute_script("g_NS_entry._saveDisclaim_rt();")
                    time.sleep(0.1)
                    
                    # 再チェック
                    entry_div = driver.find_element(By.ID, "entry")
                    entry_style = entry_div.get_attribute("class")
                    
                    if "displayNone" in entry_style:
                        print("❌ 注文フォームの表示に失敗しました")
                        return False
                    else:
                        print("✅ 注文フォームが表示されました")
                except Exception as js_e:
                    print(f"⚠️  JavaScript実行でエラー: {js_e}")
                    return False
            else:
                print("✅ 注文フォームが表示されています")
               
        except Exception as div_e:
            print(f"⚠️  注文フォーム要素の確認でエラー: {div_e}")
        
        # 通貨ペアのマッピング（HTMLの実際の値に合わせて）
        currency_pair_mapping = {
            "USDJPY": "2",     # ドル/円
            "EURJPY": "3",     # ユーロ/円  
            "EURUSD": "1",     # ユーロ/ドル
            "AUDJPY": "4",     # 豪ドル/円
            "NZDJPY": "6",     # NZドル/円
            "GBPJPY": "5",     # ポンド/円
            "CHFJPY": "8",     # スイスフラン/円
            "CADJPY": "7",     # カナダドル/円
            "GBPUSD": "9",     # ポンド/ドル
            "GBPAUD": "24",    # ポンド/豪ドル
            "ZARJPY": "10",    # ランド/円
            "TRYJPY": "23",    # トルコリラ/円
            "MXNJPY": "25",    # メキシコペソ/円
            "AUDUSD": "11",    # 豪ドル/ドル
            "NZDUSD": "12",    # NZドル/ドル
            "CNHJPY": "13",    # 人民元/円
            "HKDJPY": "14",    # 香港ドル/円
            "EURGBP": "15",    # ユーロ/ポンド
            "EURAUD": "16",    # ユーロ/豪ドル
            "USDCHF": "17",    # 米ドル/スイスフラン
            "EURCHF": "18",    # ユーロ/スイスフラン
            "GBPCHF": "19",    # ポンド/スイスフラン
            "AUDCHF": "20",    # 豪ドル/スイスフラン
            "CADCHF": "21"     # カナダドル/スイスフラン
        }
        
        # 通貨ペア選択
        try:
            pair_value = currency_pair_mapping.get(pair.upper(), "2")  # デフォルトはUSDJPY
            
            # 複数の方法で通貨ペア選択欄を探す
            try:
                pair_selector = driver.find_element(By.ID, "entryCurrencyPair")
            except NoSuchElementException:
                try:
                    pair_selector = driver.find_element(By.NAME, "currencyPair")
                except NoSuchElementException:
                    try:
                        pair_selector = driver.find_element(By.XPATH, "//select[contains(@id, 'currency') or contains(@name, 'currency') or contains(@id, 'pair')]")
                    except NoSuchElementException:
                        pair_selector = driver.find_element(By.XPATH, "//select[position()=1]")
            
            from selenium.webdriver.support.ui import Select
            select = Select(pair_selector)
            select.select_by_value(pair_value)
            
        except Exception as e:
            print(f"❌ 通貨ペア選択エラー: {e}")
            return False
        
        # 注文数量入力
        try:
            # 複数の方法で数量入力欄を探す
            try:
                amount_input = driver.find_element(By.ID, "amt_entry")
            except NoSuchElementException:
                try:
                    amount_input = driver.find_element(By.NAME, "amt")
                except NoSuchElementException:
                    try:
                        amount_input = driver.find_element(By.XPATH, "//input[@type='text' and (@id='amt' or @name='amt' or contains(@placeholder, '数量') or contains(@placeholder, '金額'))]")
                    except NoSuchElementException:
                        amount_input = driver.find_element(By.XPATH, "//input[@type='text'][position()=1]")
            
            amount_input.clear()
            amount_input.send_keys(str(amount))
            
        except Exception as e:
            print(f"❌ 注文数量入力エラー: {e}")
            return False
        
        # 買い/売りボタンの特定と実行
        try:
            if order_type.lower() == "buy":
                # 買いボタンを探す（複数の方法で試行）
                try:
                    order_button = driver.find_element(By.ID, "btn-buy_entry")
                except NoSuchElementException:
                    try:
                        # テキスト内容で検索
                        order_button = driver.find_element(By.XPATH, "//button[contains(text(), 'BUY') and contains(text(), '買')]")
                    except NoSuchElementException:
                        # より広範囲のXPath検索
                        order_button = driver.find_element(By.XPATH, "//button[contains(@class, 'buy') or contains(@id, 'buy') or contains(text(), 'BUY')]")
                
                action_name = "買い注文 (BUY)"
                button_text = order_button.text.strip()
            else:
                # 売りボタンを探す（複数の方法で試行）
                try:
                    order_button = driver.find_element(By.ID, "btn-sell_entry")
                except NoSuchElementException:
                    try:
                        # テキスト内容で検索
                        order_button = driver.find_element(By.XPATH, "//button[contains(text(), 'SELL') and contains(text(), '売')]")
                    except NoSuchElementException:
                        # より広範囲のXPath検索
                        order_button = driver.find_element(By.XPATH, "//button[contains(@class, 'sell') or contains(@id, 'sell') or contains(text(), 'SELL')]")
                
                action_name = "売り注文 (SELL)"
                button_text = order_button.text.strip()
            
            
        except NoSuchElementException:
            print(f"❌ {action_name}ボタンが見つかりません")
            return False

        # レート情報を取得（簡潔表示）
        try:
            if order_type.lower() == "buy":
                ask_price_1 = driver.find_element(By.ID, "ask-price-1_entry").text
                ask_price_2 = driver.find_element(By.ID, "ask-price-2_entry").text  
                ask_price_3 = driver.find_element(By.ID, "ask-price-3_entry").text
                current_rate = f"{ask_price_1}.{ask_price_2}{ask_price_3}"
            else:
                bid_price_1 = driver.find_element(By.ID, "bid-price-1_entry").text
                bid_price_2 = driver.find_element(By.ID, "bid-price-2_entry").text
                bid_price_3 = driver.find_element(By.ID, "bid-price-3_entry").text
                current_rate = f"{bid_price_1}.{bid_price_2}{bid_price_3}"
        except Exception:
            current_rate = "取得失敗"
        
        # 実際にボタンをクリックして注文実行
        if execute_order:
            print(f"🚀 {order_type.upper()} {pair} {amount:,} @ {current_rate}")
            
            # ボタンクリック実行
            try:
                order_button.click()
                print(f"✅ 注文実行完了")
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", order_button)
                    print(f"✅ 注文実行完了（JS）")
                except Exception as e:
                    print(f"❌ 注文実行失敗: {e}")
                    return False
            
            # 短時間の完了待機
            time.sleep(0.5)
            
            # 注文成功確認（注文完了モーダルチェック）
            try:
                complete_modal = driver.find_element(By.ID, "order-complete-modal-content")
                complete_style = complete_modal.get_attribute("class")
                if "displayNone" not in complete_style:
                    print("🎉 注文完了確認")
                    return True
            except Exception:
                pass
            
            # エラーチェック（具体的なエラー要素のみ）
            try:
                # より具体的なエラー要素を検索
                error_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@id, 'error') or (contains(text(), 'エラー') and (contains(@class, 'alert') or contains(@class, 'warning')))]")
                if error_elements:
                    # 実際にエラーメッセージが含まれているかチェック
                    for elem in error_elements:
                        text = elem.text.strip()
                        if text and len(text) > 1 and ('エラー' in text or '失敗' in text or 'error' in text.lower()):
                            print(f"❌ エラー: {text}")
                            return False
            except Exception:
                pass
            
            # エラーがなければ成功
            print("✅ 注文処理成功")
            return True
        else:
            print(f"📝 注文準備完了: {pair} {amount:,} {order_type.upper()} @ {current_rate}")
            return True
            
    except Exception as e:
        if not silent:
            print(f"❌ リアルタイム注文エラー: {e}")
        return False
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def operate_realtime_order_fast(driver, pair, amount, order_type, execute_order=True):
    """
    高速化されたリアルタイム注文実行関数
    メッセージ表示を最小限に抑制し、処理速度を優先
    """
    try:
        # 画面遷移（最小限の待機）
        if not navigate_to_order_type(driver, "realtime"):
            return False
        
        # フレーム切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 内部iframe切り替え
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if len(iframes) > 0:
            driver.switch_to.frame(iframes[0])
        
        # 通貨ペア設定
        currency_mapping = {"USDJPY": "2", "EURJPY": "3", "EURUSD": "1", "AUDJPY": "4", "GBPJPY": "5", "NZDJPY": "6"}
        pair_value = currency_mapping.get(pair.upper(), "2")
        
        pair_selector = driver.find_element(By.ID, "entryCurrencyPair")
        from selenium.webdriver.support.ui import Select
        Select(pair_selector).select_by_value(pair_value)
        
        # 数量入力
        amount_input = driver.find_element(By.ID, "amt_entry")
        amount_input.clear()
        amount_input.send_keys(str(amount))
        
        # ボタン選択とクリック
        if order_type.lower() == "buy":
            button_id = "btn-buy_entry"
        else:
            button_id = "btn-sell_entry"
        
        order_button = driver.find_element(By.ID, button_id)
        
        if execute_order:
            order_button.click()
            time.sleep(0.3)  # 最小限の待機
            print(f"🎯 高速注文完了: {order_type.upper()} {pair} {amount}")
            return True
        else:
            print(f"📝 高速注文準備: {order_type.upper()} {pair} {amount}")
            return True
            
    except Exception as e:
        print(f"❌ 高速注文エラー: {e}")
        return False
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def operate_limit_order(driver, pair="USDJPY", amount=1000, order_type="buy", 
                       limit_price=None, stop_price=None):
    """
    指値・逆指値注文を設定する関数
    
    Args:
        driver: WebDriverインスタンス
        pair: 通貨ペア（デフォルト: "USDJPY"）
        amount: 注文数量（デフォルト: 1000）
        order_type: 注文種別（"buy"または"sell"）
        limit_price: 指値価格（None の場合は設定しない）
        stop_price: 逆指値価格（None の場合は設定しない）
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"指値・逆指値注文画面を操作します（{pair}, {amount}, {order_type}）...")
        
        # 指値・逆指値注文画面に移動
        if not navigate_to_order_type(driver, "limit"):
            print("❌ 指値・逆指値注文画面への移動に失敗")
            return False
        
        time.sleep(1)
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 通貨ペア選択
        try:
            pair_selector = driver.find_element(By.NAME, "currencyPair")
            from selenium.webdriver.support.ui import Select
            select = Select(pair_selector)
            select.select_by_value(pair)
            print(f"✅ 通貨ペア {pair} を選択しました")
        except Exception as e:
            print(f"⚠️  通貨ペア選択でエラー: {e}")
        
        # 注文数量入力
        try:
            amount_input = driver.find_element(By.NAME, "orderAmount")
            amount_input.clear()
            amount_input.send_keys(str(amount))
            print(f"✅ 注文数量 {amount} を入力しました")
        except Exception as e:
            print(f"⚠️  注文数量入力でエラー: {e}")
        
        # 売買区分選択
        try:
            if order_type.lower() == "buy":
                buy_radio = driver.find_element(By.XPATH, "//input[@type='radio' and @value='1']")
                buy_radio.click()
                print("✅ 買い注文を選択しました")
            else:
                sell_radio = driver.find_element(By.XPATH, "//input[@type='radio' and @value='2']")
                sell_radio.click()
                print("✅ 売り注文を選択しました")
        except Exception as e:
            print(f"⚠️  売買区分選択でエラー: {e}")
        
        # 指値価格設定
        if limit_price is not None:
            try:
                limit_input = driver.find_element(By.NAME, "limitPrice")
                limit_input.clear()
                limit_input.send_keys(str(limit_price))
                print(f"✅ 指値価格 {limit_price} を設定しました")
            except Exception as e:
                print(f"⚠️  指値価格設定でエラー: {e}")
        
        # 逆指値価格設定
        if stop_price is not None:
            try:
                stop_input = driver.find_element(By.NAME, "stopPrice")
                stop_input.clear()
                stop_input.send_keys(str(stop_price))
                print(f"✅ 逆指値価格 {stop_price} を設定しました")
            except Exception as e:
                print(f"⚠️  逆指値価格設定でエラー: {e}")
        
        print("✅ 指値・逆指値注文の設定が完了しました")
        print("⚠️  注意: 実際の注文実行は手動で行ってください")
        print("    設定値を確認してから、注文ボタンをクリックしてください")
        
        return True
        
    except Exception as e:
        print(f"指値・逆指値注文操作でエラー: {e}")
        return False
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def operate_ifd_order(driver, pair="USDJPY", amount=1000, 
                     entry_order_type="buy", entry_price=None,
                     exit_order_type="sell", exit_price=None):
    """
    IFD注文を設定する関数
    
    Args:
        driver: WebDriverインスタンス
        pair: 通貨ペア（デフォルト: "USDJPY"）
        amount: 注文数量（デフォルト: 1000）
        entry_order_type: 新規注文種別（"buy"または"sell"）
        entry_price: 新規注文価格
        exit_order_type: 決済注文種別（"buy"または"sell"）
        exit_price: 決済注文価格
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"IFD注文画面を操作します（{pair}, {amount}）...")
        
        # IFD注文画面に移動
        if not navigate_to_order_type(driver, "ifd"):
            print("❌ IFD注文画面への移動に失敗")
            return False
        
        time.sleep(1)
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 通貨ペア選択
        try:
            pair_selector = driver.find_element(By.NAME, "currencyPair")
            from selenium.webdriver.support.ui import Select
            select = Select(pair_selector)
            select.select_by_value(pair)
            print(f"✅ 通貨ペア {pair} を選択しました")
        except Exception as e:
            print(f"⚠️  通貨ペア選択でエラー: {e}")
        
        # 注文数量入力
        try:
            amount_input = driver.find_element(By.NAME, "orderAmount")
            amount_input.clear()
            amount_input.send_keys(str(amount))
            print(f"✅ 注文数量 {amount} を入力しました")
        except Exception as e:
            print(f"⚠️  注文数量入力でエラー: {e}")
        
        # 新規注文の設定
        try:
            # 新規注文の売買区分
            if entry_order_type.lower() == "buy":
                entry_buy_radio = driver.find_element(By.XPATH, "//input[@name='entryBuySell' and @value='1']")
                entry_buy_radio.click()
                print("✅ 新規注文: 買いを選択しました")
            else:
                entry_sell_radio = driver.find_element(By.XPATH, "//input[@name='entryBuySell' and @value='2']")
                entry_sell_radio.click()
                print("✅ 新規注文: 売りを選択しました")
            
            # 新規注文の価格設定
            if entry_price is not None:
                entry_price_input = driver.find_element(By.NAME, "entryPrice")
                entry_price_input.clear()
                entry_price_input.send_keys(str(entry_price))
                print(f"✅ 新規注文価格 {entry_price} を設定しました")
                
        except Exception as e:
            print(f"⚠️  新規注文設定でエラー: {e}")
        
        # 決済注文の設定
        try:
            # 決済注文の価格設定
            if exit_price is not None:
                exit_price_input = driver.find_element(By.NAME, "exitPrice")
                exit_price_input.clear()
                exit_price_input.send_keys(str(exit_price))
                print(f"✅ 決済注文価格 {exit_price} を設定しました")
                
        except Exception as e:
            print(f"⚠️  決済注文設定でエラー: {e}")
        
        print("✅ IFD注文の設定が完了しました")
        print("⚠️  注意: 実際の注文実行は手動で行ってください")
        print("    設定値を確認してから、注文ボタンをクリックしてください")
        
        return True
        
    except Exception as e:
        print(f"IFD注文操作でエラー: {e}")
        return False
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def operate_oco_order(driver, pair="USDJPY", amount=1000,
                     first_price=None, second_price=None):
    """
    OCO注文を設定する関数
    
    Args:
        driver: WebDriverインスタンス
        pair: 通貨ペア（デフォルト: "USDJPY"）
        amount: 注文数量（デフォルト: 1000）
        first_price: 第1注文価格
        second_price: 第2注文価格
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"OCO注文画面を操作します（{pair}, {amount}）...")
        
        # OCO注文画面に移動
        if not navigate_to_order_type(driver, "oco"):
            print("❌ OCO注文画面への移動に失敗")
            return False
        
        time.sleep(1)
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 通貨ペア選択
        try:
            pair_selector = driver.find_element(By.NAME, "currencyPair")
            from selenium.webdriver.support.ui import Select
            select = Select(pair_selector)
            select.select_by_value(pair)
            print(f"✅ 通貨ペア {pair} を選択しました")
        except Exception as e:
            print(f"⚠️  通貨ペア選択でエラー: {e}")
        
        # 注文数量入力
        try:
            amount_input = driver.find_element(By.NAME, "orderAmount")
            amount_input.clear()
            amount_input.send_keys(str(amount))
            print(f"✅ 注文数量 {amount} を入力しました")
        except Exception as e:
            print(f"⚠️  注文数量入力でエラー: {e}")
        
        # 第1注文価格設定
        if first_price is not None:
            try:
                first_price_input = driver.find_element(By.NAME, "firstPrice")
                first_price_input.clear()
                first_price_input.send_keys(str(first_price))
                print(f"✅ 第1注文価格 {first_price} を設定しました")
            except Exception as e:
                print(f"⚠️  第1注文価格設定でエラー: {e}")
        
        # 第2注文価格設定
        if second_price is not None:
            try:
                second_price_input = driver.find_element(By.NAME, "secondPrice")
                second_price_input.clear()
                second_price_input.send_keys(str(second_price))
                print(f"✅ 第2注文価格 {second_price} を設定しました")
            except Exception as e:
                print(f"⚠️  第2注文価格設定でエラー: {e}")
        
        print("✅ OCO注文の設定が完了しました")
        print("⚠️  注意: 実際の注文実行は手動で行ってください")
        print("    設定値を確認してから、注文ボタンをクリックしてください")
        
        return True
        
    except Exception as e:
        print(f"OCO注文操作でエラー: {e}")
        return False
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def operate_ifo_order(driver, pair="USDJPY", amount=1000,
                     entry_order_type="buy", entry_price=None,
                     profit_price=None, loss_price=None):
    """
    IFO注文を設定する関数（IFD + OCO）
    
    Args:
        driver: WebDriverインスタンス
        pair: 通貨ペア（デフォルト: "USDJPY"）
        amount: 注文数量（デフォルト: 1000）
        entry_order_type: 新規注文種別（"buy"または"sell"）
        entry_price: 新規注文価格
        profit_price: 利益確定価格
        loss_price: 損切り価格
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"IFO注文画面を操作します（{pair}, {amount}）...")
        
        # IFO注文画面に移動
        if not navigate_to_order_type(driver, "ifo"):
            print("❌ IFO注文画面への移動に失敗")
            return False
        
        time.sleep(1)
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 通貨ペア選択
        try:
            pair_selector = driver.find_element(By.NAME, "currencyPair")
            from selenium.webdriver.support.ui import Select
            select = Select(pair_selector)
            select.select_by_value(pair)
            print(f"✅ 通貨ペア {pair} を選択しました")
        except Exception as e:
            print(f"⚠️  通貨ペア選択でエラー: {e}")
        
        # 注文数量入力
        try:
            amount_input = driver.find_element(By.NAME, "orderAmount")
            amount_input.clear()
            amount_input.send_keys(str(amount))
            print(f"✅ 注文数量 {amount} を入力しました")
        except Exception as e:
            print(f"⚠️  注文数量入力でエラー: {e}")
        
        # 新規注文の設定
        try:
            # 新規注文の売買区分
            if entry_order_type.lower() == "buy":
                entry_buy_radio = driver.find_element(By.XPATH, "//input[@name='entryBuySell' and @value='1']")
                entry_buy_radio.click()
                print("✅ 新規注文: 買いを選択しました")
            else:
                entry_sell_radio = driver.find_element(By.XPATH, "//input[@name='entryBuySell' and @value='2']")
                entry_sell_radio.click()
                print("✅ 新規注文: 売りを選択しました")
            
            # 新規注文の価格設定
            if entry_price is not None:
                entry_price_input = driver.find_element(By.NAME, "entryPrice")
                entry_price_input.clear()
                entry_price_input.send_keys(str(entry_price))
                print(f"✅ 新規注文価格 {entry_price} を設定しました")
                
        except Exception as e:
            print(f"⚠️  新規注文設定でエラー: {e}")
        
        # 利益確定価格設定
        if profit_price is not None:
            try:
                profit_price_input = driver.find_element(By.NAME, "profitPrice")
                profit_price_input.clear()
                profit_price_input.send_keys(str(profit_price))
                print(f"✅ 利益確定価格 {profit_price} を設定しました")
            except Exception as e:
                print(f"⚠️  利益確定価格設定でエラー: {e}")
        
        # 損切り価格設定
        if loss_price is not None:
            try:
                loss_price_input = driver.find_element(By.NAME, "lossPrice")
                loss_price_input.clear()
                loss_price_input.send_keys(str(loss_price))
                print(f"✅ 損切り価格 {loss_price} を設定しました")
            except Exception as e:
                print(f"⚠️  損切り価格設定でエラー: {e}")
        
        print("✅ IFO注文の設定が完了しました")
        print("⚠️  注意: 実際の注文実行は手動で行ってください")
        print("    設定値を確認してから、注文ボタンをクリックしてください")
        
        return True
        
    except Exception as e:
        print(f"IFO注文操作でエラー: {e}")
        return False
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def analyze_form_elements(driver, order_type="realtime"):
    """
    指定された注文タイプ画面のフォーム要素を詳細分析する関数
    
    Args:
        driver: WebDriverインスタンス
        order_type: 分析する注文タイプ
    """
    try:
        print(f"\n=== {order_type.upper()} 画面のフォーム要素分析 ===")
        
        # 指定された注文タイプに移動
        if not navigate_to_order_type(driver, order_type):
            print(f"❌ {order_type} 画面への移動に失敗")
            return
        
        time.sleep(0.1)
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 全ての入力要素を分析
        input_elements = driver.find_elements(By.TAG_NAME, "input")
        select_elements = driver.find_elements(By.TAG_NAME, "select")
        
        #print(f"入力要素 ({len(input_elements)}個):")
        for i, elem in enumerate(input_elements):
            try:
                elem_type = elem.get_attribute("type") or "text"
                elem_name = elem.get_attribute("name") or "no-name"
                elem_id = elem.get_attribute("id") or "no-id"
                elem_value = elem.get_attribute("value") or ""
                elem_class = elem.get_attribute("class") or "no-class"
                
                #print(f"  input[{i}]: type={elem_type}, name={elem_name}, id={elem_id}")
                if elem_value:
                    #print(f"             value={elem_value[:50]}...")
                    print("")
                if elem_class != "no-class":
                    #print(f"             class={elem_class}")
                    print("")
                    
            except Exception:
                print(f"  input[{i}]: 要素情報取得エラー")
        
        #print(f"\nセレクト要素 ({len(select_elements)}個):")
        for i, elem in enumerate(select_elements):
            try:
                elem_name = elem.get_attribute("name") or "no-name"
                elem_id = elem.get_attribute("id") or "no-id"
                options = elem.find_elements(By.TAG_NAME, "option")
                
                #print(f"  select[{i}]: name={elem_name}, id={elem_id}")
                #print(f"              options={len(options)}個")
                
                # 最初の3つのオプション値を表示
                for j, option in enumerate(options[:3]):
                    option_value = option.get_attribute("value") or ""
                    option_text = option.text.strip()
                    #print(f"                [{j}] value={option_value}, text={option_text}")
                
                if len(options) > 3:
                    #print(f"                ... 他{len(options)-3}個")
                    print(""   )

            except Exception:
                print(f"  select[{i}]: 要素情報取得エラー")
        
        # ボタン要素を分析
        button_elements = driver.find_elements(By.XPATH, "//input[@type='submit'] | //input[@type='button'] | //button")
        
        #print(f"\nボタン要素 ({len(button_elements)}個):")
        for i, elem in enumerate(button_elements):
            try:
                elem_type = elem.get_attribute("type") or "button"
                elem_value = elem.get_attribute("value") or ""
                elem_text = elem.text.strip()
                elem_onclick = elem.get_attribute("onclick") or ""
                
                #print(f"  button[{i}]: type={elem_type}")
                if elem_value:
                    #print(f"              value={elem_value}")
                    print("")
                if elem_text:
                    #print(f"              text={elem_text}")
                    print("")
                if elem_onclick:
                    #print(f"              onclick={elem_onclick[:50]}...")
                    print("")

            except Exception:
                print(f"  button[{i}]: 要素情報取得エラー")
        
        print(f"\n=== {order_type.upper()} 画面の分析完了 ===\n")
        
    except Exception as e:
        print(f"フォーム要素分析でエラー: {e}")
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def demonstrate_order_operations(driver):
    """
    各注文タイプの操作をデモンストレーションする関数
    """
    print("\n=== 各注文タイプの操作デモンストレーション ===")
    
    operations = [
        {
            "name": "リアルタイム注文",
            "function": lambda: operate_realtime_order(driver, "USDJPY", 1000, "buy")
        },
        {
            "name": "指値・逆指値注文", 
            "function": lambda: operate_limit_order(driver, "USDJPY", 1000, "buy", 
                                                   limit_price=150.00, stop_price=149.50)
        },
        {
            "name": "IFD注文",
            "function": lambda: operate_ifd_order(driver, "USDJPY", 1000, 
                                                 "buy", 149.80, "sell", 150.20)
        },
        {
            "name": "OCO注文",
            "function": lambda: operate_oco_order(driver, "USDJPY", 1000, 
                                                 150.20, 149.50)
        },
        {
            "name": "IFO注文",
            "function": lambda: operate_ifo_order(driver, "USDJPY", 1000, 
                                                 "buy", 149.80, 150.20, 149.50)
        }
    ]
    
    for operation in operations:
        print(f"\n--- {operation['name']} のデモ ---")
        try:
            success = operation["function"]()
            if success:
                print(f"✅ {operation['name']} の設定が完了しました")
            else:
                print(f"❌ {operation['name']} の設定に失敗しました")
        except Exception as e:
            print(f"❌ {operation['name']} でエラー: {e}")
        
        # 各操作の間に少し待機
        time.sleep(1)
    
    print("\n=== デモンストレーション完了 ===")
    print("⚠️  注意: 実際の取引は行われていません")
    print("    各画面で設定を確認してから手動で実行してください")


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
            
            # リアルタイム注文のテスト（デフォルト値でテスト）
            print("\n--- リアルタイム注文（execute_order=True）のテスト ---")
            operate_realtime_order(driver, "USDJPY", 20000, "sell", execute_order=True)  # 明示的にTrue指定
            
            # 利用可能な注文タイプを表示
            #display_available_order_types()
            
            # 各注文タイプの操作デモ
            #demonstrate_order_operations(driver)
            

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
