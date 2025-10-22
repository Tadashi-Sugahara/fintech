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
    """Ctrl+C（SIGINT）が押された時のハンドラー - ChromeDriverのブラウザのみ閉じる"""
    print("\n\n🛑 Ctrl+C が検出されました")
    print("ChromeDriverで開いたブラウザのみを閉じます...")
    
    try:
        if global_driver:
            # ChromeDriverのブラウザを閉じる
            global_driver.quit()
            print("✅ ChromeDriverのブラウザを閉じました")
        else:
            print("⚠️  アクティブなChromeDriverが見つかりません")
    except Exception as e:
        print(f"⚠️  ブラウザ終了エラー: {e}")
    
    try:
        # ChromeDriverプロセスのみを対象とした軽度なクリーンアップ
        # 他のChromeブラウザには影響しない
        from kill_process import cleanup_driver_selective
        cleanup_driver_selective()
        print("✅ ChromeDriverプロセスのクリーンアップ完了")
    except Exception as e:
        print(f"⚠️  クリーンアップエラー: {e}")
    
    print("🏁 ブラウザ終了処理が完了しました")
    print("💡 プログラムを終了するには再度 Ctrl+C を押してください")

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

def cleanup_driver_selective():
    """ChromeDriverで起動されたブラウザのみを対象とした軽度なクリーンアップ"""
    import psutil
    import subprocess
    
    try:
        print("🔍 ChromeDriverプロセスを検索中...")
        
        # ChromeDriverプロセスのPIDを取得
        chromedriver_pids = []
        chrome_with_test_type_pids = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'chromedriver' in proc.info['name'].lower():
                    chromedriver_pids.append(proc.info['pid'])
                    print(f"  📍 ChromeDriver発見: PID {proc.info['pid']}")
                
                # --test-typeオプション付きのChromeプロセスを探す
                if proc.info['cmdline'] and proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    cmdline_str = ' '.join(proc.info['cmdline'])
                    if '--test-type' in cmdline_str or '--disable-dev-shm-usage' in cmdline_str:
                        chrome_with_test_type_pids.append(proc.info['pid'])
                        print(f"  🎯 ChromeDriver制御下のChrome発見: PID {proc.info['pid']}")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # ChromeDriverで起動されたChromeプロセスのみを終了
        terminated_count = 0
        for pid in chrome_with_test_type_pids:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                print(f"  ✅ Chrome終了: PID {pid}")
                terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # ChromeDriverプロセスを終了
        for pid in chromedriver_pids:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                print(f"  ✅ ChromeDriver終了: PID {pid}")
                terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if terminated_count > 0:
            print(f"✅ {terminated_count}個のChromeDriver関連プロセスを終了しました")
            time.sleep(1)  # プロセス終了を待機
        else:
            print("ℹ️  終了対象のChromeDriverプロセスが見つかりませんでした")
            
    except Exception as e:
        print(f"⚠️  選択的クリーンアップでエラー: {e}")


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
