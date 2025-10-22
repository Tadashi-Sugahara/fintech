#!/usr/bin/env python3
"""
ブラウザ安定性診断ツール
使用方法：python browser_diagnostics.py
"""

import psutil
import platform
import os
import time
from datetime import datetime

def check_system_resources():
    """システムリソースの状況を確認"""
    print("=== システムリソース診断 ===")
    
    # CPU使用率
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"CPU使用率: {cpu_percent}%")
    
    # メモリ使用率
    memory = psutil.virtual_memory()
    print(f"メモリ使用率: {memory.percent}% ({memory.used // 1024**2}MB / {memory.total // 1024**2}MB)")
    
    # ディスク使用率
    disk = psutil.disk_usage('/')
    print(f"ディスク使用率: {disk.percent}% ({disk.used // 1024**3}GB / {disk.total // 1024**3}GB)")
    
    # 警告レベルのチェック
    warnings = []
    if cpu_percent > 80:
        warnings.append("⚠️  CPU使用率が高すぎます")
    if memory.percent > 85:
        warnings.append("⚠️  メモリ使用率が高すぎます")
    if disk.percent > 90:
        warnings.append("⚠️  ディスク容量が不足しています")
    
    if warnings:
        print("\n🔴 警告:")
        for warning in warnings:
            print(f"  {warning}")
    else:
        print("\n✅ システムリソースは正常です")

def check_chrome_processes():
    """Chrome関連プロセスの状況を確認"""
    print("\n=== Chrome関連プロセス診断 ===")
    
    chrome_processes = []
    chromedriver_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
            try:
                if not proc.info['name']:
                    continue
                    
                name_lower = proc.info['name'].lower()
                
                if 'chromedriver' in name_lower:
                    chromedriver_processes.append(proc.info)
                elif 'chrome' in name_lower:
                    chrome_processes.append(proc.info)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    except Exception as e:
        print(f"❌ プロセス検索エラー: {e}")
        return
    
    print(f"ChromeDriverプロセス: {len(chromedriver_processes)}個")
    for proc in chromedriver_processes:
        memory_mb = proc['memory_info'].rss / 1024 / 1024 if proc['memory_info'] else 0
        print(f"  PID {proc['pid']}: メモリ {memory_mb:.1f}MB")
    
    print(f"Chromeプロセス: {len(chrome_processes)}個")
    total_chrome_memory = 0
    for proc in chrome_processes:
        memory_mb = proc['memory_info'].rss / 1024 / 1024 if proc['memory_info'] else 0
        total_chrome_memory += memory_mb
        if memory_mb > 100:  # 100MB以上のプロセスのみ表示
            print(f"  PID {proc['pid']}: メモリ {memory_mb:.1f}MB")
    
    print(f"Chrome総メモリ使用量: {total_chrome_memory:.1f}MB")
    
    # 異常な状況のチェック
    if len(chromedriver_processes) > 5:
        print("⚠️  ChromeDriverプロセスが多すぎます（ゾンビプロセスの可能性）")
    if len(chrome_processes) > 20:
        print("⚠️  Chromeプロセスが多すぎます")
    if total_chrome_memory > 2000:
        print("⚠️  Chromeのメモリ使用量が多すぎます")

def check_temp_directories():
    """一時ディレクトリの状況を確認"""
    print("\n=== 一時ディレクトリ診断 ===")
    
    import tempfile
    temp_dir = tempfile.gettempdir()
    chrome_profile_dir = os.path.join(temp_dir, 'chrome_automation_profile_stable')
    
    print(f"一時ディレクトリ: {temp_dir}")
    
    try:
        # 一時ディレクトリのサイズチェック
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except:
                    pass
        
        print(f"一時ディレクトリ使用量: {total_size // 1024 // 1024}MB ({file_count}ファイル)")
        
        # Chromeプロファイルディレクトリの確認
        if os.path.exists(chrome_profile_dir):
            profile_size = 0
            try:
                for root, dirs, files in os.walk(chrome_profile_dir):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            profile_size += os.path.getsize(file_path)
                        except:
                            pass
                print(f"Chromeプロファイル使用量: {profile_size // 1024 // 1024}MB")
            except Exception as e:
                print(f"プロファイルサイズ取得エラー: {e}")
        else:
            print("Chromeプロファイルディレクトリ: 存在しません（正常）")
        
        if total_size > 1024 * 1024 * 1024:  # 1GB以上
            print("⚠️  一時ディレクトリが大きすぎます（クリーンアップを推奨）")
        
    except Exception as e:
        print(f"❌ 一時ディレクトリ確認エラー: {e}")

def check_chrome_installation():
    """Chrome/ChromeDriverのインストール状況を確認"""
    print("\n=== Chrome/ChromeDriverインストール診断 ===")
    
    # Chrome実行ファイルのパス候補
    chrome_paths = []
    if platform.system() == 'Windows':
        chrome_paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        ]
    else:
        chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        ]
    
    print("Chrome実行ファイル:")
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"  ✅ {path}")
            chrome_found = True
        else:
            print(f"  ❌ {path}")
    
    if not chrome_found:
        print("⚠️  Chrome実行ファイルが見つかりません")
    
    # ChromeDriverのパス候補
    chromedriver_paths = []
    if platform.system() == 'Windows':
        chromedriver_paths = [
            r'C:\chromedriver\chromedriver.exe',
            r'C:\Program Files\ChromeDriver\chromedriver.exe',
        ]
    else:
        chromedriver_paths = [
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
        ]
    
    print("ChromeDriver実行ファイル:")
    chromedriver_found = False
    for path in chromedriver_paths:
        if os.path.exists(path):
            print(f"  ✅ {path}")
            chromedriver_found = True
        else:
            print(f"  ❌ {path}")
    
    # 環境変数のチェック
    chrome_binary = os.environ.get('CHROME_BINARY')
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
    
    if chrome_binary:
        print(f"CHROME_BINARY環境変数: {chrome_binary}")
    if chromedriver_path:
        print(f"CHROMEDRIVER_PATH環境変数: {chromedriver_path}")

def main():
    print("🔍 ブラウザ安定性診断ツール")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print("=" * 60)
    
    check_system_resources()
    check_chrome_processes()
    check_temp_directories()
    check_chrome_installation()
    
    print("\n" + "=" * 60)
    print("🏁 診断完了")
    print("\n💡 推奨事項:")
    print("  - システムリソースが不足している場合は、他のアプリケーションを終了してください")
    print("  - Chrome関連プロセスが多すぎる場合は、手動で終了するか再起動してください")
    print("  - 一時ディレクトリが大きすぎる場合は、ディスククリーンアップを実行してください")

if __name__ == "__main__":
    main()