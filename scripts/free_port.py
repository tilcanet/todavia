import subprocess
import os
import signal
import re
import sys

# Puerto que queremos liberar
PORT = 8000

def get_pids_using_ss(port):
    """Obtiene PIDs usando el comando ss (que el usuario tiene instalado)"""
    pids = set()
    try:
        # Ejecutamos ss -lptn 'sport = :8000'
        # -l: listening, -p: processes, -t: tcp, -n: numeric
        cmd = ['ss', '-lptn', f'sport = :{port}']
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8')
        
        # Buscamos patrones como pid=1234
        for line in output.splitlines():
            matches = re.findall(r'pid=(\d+)', line)
            for pid in matches:
                pids.add(int(pid))
    except Exception as e:
        print(f"⚠️ Error ejecutando ss: {e}")
    return pids

def kill_pids(pids):
    if not pids:
        print(f"✅ Puerto {PORT} libre.")
        return

    print(f"🧹 Liberando puerto {PORT}. Procesos encontrados: {pids}")
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
            print(f"   🔫 Kill PID {pid}")
        except ProcessLookupError:
            print(f"   💨 PID {pid} ya no existe.")
        except PermissionError:
            print(f"   ⛔ Permiso denegado para PID {pid} (¿Eres root?)")
        except Exception as e:
            print(f"   ⚠️ Error matando {pid}: {e}")

if __name__ == '__main__':
    print(f"🔍 Buscando procesos en puerto {PORT}...")
    pids = get_pids_using_ss(PORT)
    kill_pids(pids)
