#!/usr/bin/env python3
"""
Chrome関連プロセス確認・終了ツール
使用方法：
  python check_chrome_processes.py         # プロセス確認のみ
  python check_chrome_processes.py kill    # プロセス終了も実行
"""

import psutil
import sys
import time

def find_chrome_processes():
    """Chrome関連プロセスを検索する"""
    chrome_processes = []
    chromedriver_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if not proc.info['name'] or not proc.info['cmdline']:
                    continue
                    
                name_lower = proc.info['name'].lower()
                cmdline_str = ' '.join(proc.info['cmdline']).lower()
                
                # ChromeDriverプロセス
                if 'chromedriver' in name_lower:
                    chromedriver_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': ' '.join(proc.info['cmdline']),
                        'create_time': proc.info['create_time'],
                        'type': 'ChromeDriver'
                    })
                
                # Chrome自動化プロセス（特定の引数を持つ）
                elif 'chrome' in name_lower and any(flag in cmdline_str for flag in [
                    '--test-type', '--disable-dev-shm-usage', '--no-sandbox', 
                    '--disable-gpu', '--disable-extensions', '--disable-web-security'
                ]):
                    chrome_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': ' '.join(proc.info['cmdline']),
                        'create_time': proc.info['create_time'],
                        'type': 'Chrome自動化'
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    
    except Exception as e:
        print(f"❌ プロセス検索でエラー: {e}")
    
    return chromedriver_processes + chrome_processes

def display_processes(processes):
    """プロセス一覧を表示する"""
    if not processes:
        print("✅ Chrome関連の残存プロセスはありません")
        return
    
    print(f"\n🔍 {len(processes)}個のChrome関連プロセスが見つかりました:")
    print("-" * 80)
    
    for proc in processes:
        create_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(proc['create_time']))
        print(f"📍 {proc['type']}")
        print(f"   PID: {proc['pid']}")
        print(f"   名前: {proc['name']}")
        print(f"   開始時刻: {create_time_str}")
        print(f"   コマンド: {proc['cmdline'][:100]}{'...' if len(proc['cmdline']) > 100 else ''}")
        print("-" * 80)

def kill_processes(processes):
    """プロセスを終了する"""
    if not processes:
        print("✅ 終了対象のプロセスはありません")
        return
    
    print(f"\n💀 {len(processes)}個のプロセスを終了します...")
    
    terminated_count = 0
    killed_count = 0
    
    # 段階1: terminate()で優しく終了
    for proc_info in processes:
        try:
            proc = psutil.Process(proc_info['pid'])
            proc.terminate()
            print(f"  ✅ terminate(): PID {proc_info['pid']} ({proc_info['type']})")
            terminated_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print(f"  ⚠️  アクセス不可: PID {proc_info['pid']}")
        except Exception as e:
            print(f"  ❌ terminate()エラー: PID {proc_info['pid']} - {e}")
    
    if terminated_count > 0:
        print(f"⏳ {terminated_count}個のプロセス終了を3秒間待機...")
        time.sleep(3)
    
    # 段階2: まだ残っているプロセスをkill()で強制終了
    remaining_processes = find_chrome_processes()
    if remaining_processes:
        print("🔧 残存プロセスを強制終了中...")
        for proc_info in remaining_processes:
            try:
                proc = psutil.Process(proc_info['pid'])
                proc.kill()
                print(f"  💀 kill(): PID {proc_info['pid']} ({proc_info['type']})")
                killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"  ⚠️  アクセス不可: PID {proc_info['pid']}")
            except Exception as e:
                print(f"  ❌ kill()エラー: PID {proc_info['pid']} - {e}")
    
    print(f"\n📊 終了処理結果:")
    print(f"   terminate(): {terminated_count}個")
    print(f"   kill(): {killed_count}個")
    
    # 最終確認
    time.sleep(1)
    final_processes = find_chrome_processes()
    if final_processes:
        print(f"⚠️  {len(final_processes)}個のプロセスが残存しています")
        display_processes(final_processes)
    else:
        print("✅ 全てのChrome関連プロセスが終了しました")

def main():
    print("🔍 Chrome関連プロセス確認・終了ツール")
    print("=" * 50)
    
    # プロセス検索
    processes = find_chrome_processes()
    display_processes(processes)
    
    # 引数に'kill'があれば終了処理も実行
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'kill':
        if processes:
            print("\n❓ 本当にこれらのプロセスを終了しますか？")
            response = input("終了する場合は 'yes' と入力してください: ")
            if response.lower() == 'yes':
                kill_processes(processes)
            else:
                print("🚫 プロセス終了をキャンセルしました")
        else:
            print("✅ 終了対象のプロセスはありません")
    else:
        if processes:
            print("\n💡 これらのプロセスを終了するには:")
            print("   python check_chrome_processes.py kill")

if __name__ == "__main__":
    main()