import os
import platform
import signal
import subprocess
import time
import atexit
import psutil

def kill_chrome():
    #Chromeプロセスを強制終了する関数
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
    try:  # シグナル
        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)  # 終了シグナル
    except Exception as e:
        print(f"シグナルハンドラーの登録に失敗: {e}")

    # プログラム終了時の自動クリーンアップ
    atexit.register(cleanup_driver)
