"""Portable Windows GUI entry point; also dispatches worker subprocesses."""
import sys
from pathlib import Path
# Frozen one-folder builds keep editable data beside the EXE, not in _internal.
BASE=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent

def worker():
    import macro
    import json
    macro.ROOT=BASE
    c=json.loads((BASE/'config.json').read_text())
    if '--capture-prompt' in sys.argv:
        import time, mss, cv2, numpy as np
        print('Capturing prompt ROI in 5 seconds. Focus Roblox now.',flush=True)
        time.sleep(5)
        x,y,w,h=c['prompt_roi']
        with mss.mss() as sct:
            im=np.array(sct.grab(dict(left=x,top=y,width=w,height=h)))[:,:,:3]
        cv2.imwrite(str(BASE/'data/e_prompt.png'),im)
        print('Saved data/e_prompt.png. Crop it to the stable E icon before running.',flush=True)
    else:
        if not c.get('calibrated'): raise RuntimeError('Calibrate first, then set calibrated to true in settings.')
        macro.Bot(c).run()

def main():
    import tkinter as tk
    from tkinter import ttk,messagebox
    import json,subprocess,threading,queue,os
    root=tk.Tk(); root.title('Spooksville • Portable Macro'); root.geometry('860x760')
    root.minsize(700,600)
    style=ttk.Style(); style.theme_use('clam')
    style.configure('TButton',padding=8)
    frame=ttk.Frame(root,padding=18); frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Spooksville Macro',font=('Segoe UI',23,'bold')).pack(anchor='w')
    ttk.Label(frame,text='Calibration required • F7 resume · F6 pause · F8 exit worker',font=('Segoe UI',10)).pack(anchor='w',pady=(4,10))
    ttk.Label(frame,text='Requires a fixed full-map view with a visible player marker. Scrolling minimaps are unsupported.',wraplength=790).pack(anchor='w',pady=(0,12))
    bar=ttk.Frame(frame); bar.pack(fill='x')
    process=[None]; messages=queue.Queue()
    status=tk.StringVar(value='Stopped')
    def open_file(path):
        try: os.startfile(str(BASE/path))
        except Exception as e: messagebox.showerror('Open file',str(e))
    def save():
        try:
            c=json.loads(editor.get('1.0','end'))
            for key in ('map_roi','prompt_roi'):
                if len(c[key])!=4 or any(not isinstance(v,int) for v in c[key]) or min(c[key][2:])<=0: raise ValueError(key+' must contain integer left, top, positive width, height')
            if c['grid_scale']<=0 or c['clearance_px']<1: raise ValueError('Invalid grid scale or clearance')
            w,d=c['w_map_vector'],c['d_map_vector']
            if abs(w[0]*d[1]-w[1]*d[0])<.001: raise ValueError('W and D vectors must not be parallel')
            (BASE/'config.json').write_text(json.dumps(c,indent=2)); return True
        except Exception as e: messagebox.showerror('Settings not saved',str(e)); return False
    def start(capture=False):
        if process[0] and process[0].poll() is None: messagebox.showinfo('Already running','Stop the current worker first.'); return
        if not save(): return
        if not capture and not json.loads((BASE/'config.json').read_text()).get('calibrated'):
            messagebox.showwarning('Calibration needed','Read the guide and calibrate settings before setting calibrated to true.'); return
        args=[sys.executable]
        if not getattr(sys,'frozen',False): args += [str(Path(__file__).resolve())]
        args += ['--worker']+(['--capture-prompt'] if capture else [])
        env=os.environ.copy(); env['PYTHONUNBUFFERED']='1'
        try: process[0]=subprocess.Popen(args,cwd=BASE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except Exception as e: messagebox.showerror('Could not start',str(e)); return
        p=process[0]; status.set('Capturing in 5 seconds' if capture else 'Worker ready — focus Roblox and press F7')
        def read():
            for line in p.stdout: messages.put(line)
            p.wait(); messages.put('\nWorker exited: '+str(p.returncode)+'\n')
        threading.Thread(target=read,daemon=True).start()
    def stop():
        # Prefer the worker's normal F8 exit; hard termination can bypass key release.
        p=process[0]
        if p and p.poll() is None:
            try:
                import keyboard
                keyboard.press_and_release('f8')
                status.set('Exit requested — waiting for worker')
            except Exception as e: messagebox.showerror('Stop','Press F8 in Roblox to exit. '+str(e))
    ttk.Button(bar,text='Start macro',command=start).pack(side='left',padx=(0,6))
    ttk.Button(bar,text='Stop (F8)',command=stop).pack(side='left',padx=6)
    ttk.Button(bar,text='Capture E prompt',command=lambda:start(True)).pack(side='left',padx=6)
    links=ttk.Frame(frame); links.pack(fill='x',pady=8)
    for label,path in [('Door editor','tools/door_editor.html'),('User guide','README.md'),('Open app folder','.'),('Prompt image','data/e_prompt.png')]:
        ttk.Button(links,text=label,command=lambda p=path:open_file(p)).pack(side='left',padx=(0,6))
    ttk.Label(frame,textvariable=status).pack(anchor='w',pady=(0,8))
    ttk.Label(frame,text='Settings (JSON) — save before starting',font=('Segoe UI',11,'bold')).pack(anchor='w')
    editor=tk.Text(frame,height=15,wrap='none',font=('Consolas',10),undo=True)
    editor.pack(fill='both',expand=True,pady=6)
    editor.insert('1.0',(BASE/'config.json').read_text())
    ttk.Button(frame,text='Save settings',command=save).pack(anchor='w')
    ttk.Label(frame,text='Activity log').pack(anchor='w',pady=(8,0))
    log=tk.Text(frame,height=7,state='disabled',font=('Consolas',9)); log.pack(fill='x',pady=5)
    def poll():
        while not messages.empty():
            log.configure(state='normal'); log.insert('end',messages.get()); log.see('end'); log.configure(state='disabled')
        if process[0] and process[0].poll() is not None: status.set('Stopped')
        root.after(150,poll)
    def close():
        if process[0] and process[0].poll() is None:
            stop(); messagebox.showinfo('Exit worker first','Wait for the worker to stop, then close this window. If necessary, press F8.'); return
        root.destroy()
    root.protocol('WM_DELETE_WINDOW',close); poll(); root.mainloop()

if __name__=='__main__':
    if '--worker' in sys.argv:
        try: worker()
        except Exception:
            import traceback
            traceback.print_exc(); sys.exit(1)
    else: main()
