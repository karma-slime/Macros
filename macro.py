"""Calibrated screen-input prototype. See README before enabling movement."""
import argparse, heapq, json, math, time
from pathlib import Path
import cv2
import numpy as np
ROOT = Path(__file__).resolve().parent

def astar(mask, start, goal):
    h,w=mask.shape
    q=[(0,0,start)]; costs={start:0}; prev={}
    while q:
        _,g,p=heapq.heappop(q)
        if g != costs[p]: continue
        if p==goal:
            route=[p]
            while p in prev: p=prev[p]; route.append(p)
            return route[::-1]
        x,y=p
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            n=(x+dx,y+dy); nx,ny=n
            if not (0<=nx<w and 0<=ny<h) or not mask[ny,nx]: continue
            if dx and dy and (not mask[y,nx] or not mask[ny,x]): continue
            ng=g+math.hypot(dx,dy)
            if ng<costs.get(n,float('inf')):
                costs[n]=ng; prev[n]=p
                heapq.heappush(q,(ng+math.dist(n,goal),ng,n))
    return None

def snap(mask,p):
    yy,xx=np.nonzero(mask)
    if not len(xx): raise RuntimeError('No walkable pixels')
    i=np.argmin((xx-p[0])**2+(yy-p[1])**2)
    return int(xx[i]),int(yy[i])

class Bot:
    def __init__(self,c):
        import mss, pydirectinput, keyboard
        self.sct=mss.mss(); self.keys=pydirectinput; self.kb=keyboard; self.c=c
        self.keys.PAUSE=0.01
        self.doors=json.loads((ROOT/'data/doors.json').read_text())['doors']
        self.scale=c['grid_scale']
        raw=cv2.imread(str(ROOT/'data/nav_full.png'),0)
        raw=cv2.erode(raw,np.ones((c['clearance_px'],)*2,np.uint8))
        self.mask=cv2.resize(raw,None,fx=1/self.scale,fy=1/self.scale,interpolation=cv2.INTER_NEAREST)>127
        self.ledger_path=ROOT/'cooldowns.json'
        self.ledger=json.loads(self.ledger_path.read_text()) if self.ledger_path.exists() else {}
        self.template=cv2.imread(str(ROOT/'data/e_prompt.png'),0)
        if self.template is None: raise RuntimeError('Capture data/e_prompt.png first')
        self.active=False; self.held=set()
    def grab(self,roi):
        x,y,w,h=roi
        return np.array(self.sct.grab(dict(left=x,top=y,width=w,height=h)))[:,:,:3]
    def release(self):
        for k in list(self.held): self.keys.keyUp(k)
        self.held.clear()
    def position(self):
        im=self.grab(self.c['map_roi']); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
        m=cv2.inRange(hsv,np.array(self.c['marker_hsv_low']),np.array(self.c['marker_hsv_high']))
        n,labels,stats,cent=cv2.connectedComponentsWithStats(m)
        candidates=[i for i in range(1,n) if self.c['marker_min_area']<=stats[i,4]<=self.c['marker_max_area']]
        if len(candidates)!=1: raise RuntimeError('Player marker missing or ambiguous; paused')
        x,y=cent[candidates[0]]; _,_,w,h=self.c['map_roi']
        return x/w*self.c['map_size'][0],y/h*self.c['map_size'][1]
    def prompt(self):
        im=cv2.cvtColor(self.grab(self.c['prompt_roi']),cv2.COLOR_BGR2GRAY)
        if any(a>b for a,b in zip(self.template.shape,im.shape)): raise RuntimeError('Prompt template larger than ROI')
        return cv2.minMaxLoc(cv2.matchTemplate(im,self.template,cv2.TM_CCOEFF_NORMED))[1]>=self.c['prompt_threshold']
    def interrupt(self):
        if self.kb.is_pressed('f8'): raise KeyboardInterrupt
        if self.kb.is_pressed('f6'):
            self.active=False; self.release(); return True
        return False
    def wait(self,seconds):
        until=time.monotonic()+seconds
        while time.monotonic()<until:
            if self.interrupt(): return False
            time.sleep(.05)
        return True
    def move(self,p,target):
        delta=np.array(target)-p
        # Columns: map-space unit directions for W and D; calibrated by user.
        matrix=np.array([self.c['w_map_vector'],self.c['d_map_vector']],float).T
        a,b=np.linalg.solve(matrix,delta)
        wanted=set()
        if abs(a)>.35*max(abs(a),abs(b)): wanted.add('w' if a>0 else 's')
        if abs(b)>.35*max(abs(a),abs(b)): wanted.add('d' if b>0 else 'a')
        for k in self.held-wanted: self.keys.keyUp(k)
        for k in wanted-self.held: self.keys.keyDown(k)
        self.held=wanted
    def plan(self,p):
        mask=self.mask.copy(); now=time.time(); s=self.scale
        for d in self.doors:
            if self.ledger.get(str(d['id']),0)>now:
                cv2.circle(mask.view(np.uint8),(round(d['x']/s),round(d['y']/s)),max(1,round(self.c['cooldown_avoid_px']/s)),0,-1)
        start=snap(mask,(p[0]/s,p[1]/s))
        choices=[]
        for d in self.doors:
            if self.ledger.get(str(d['id']),0)>now: continue
            goal=snap(mask,(d['x']/s,d['y']/s))
            if math.dist(goal,(d['x']/s,d['y']/s))*s>self.c['max_door_snap_px']: continue
            route=astar(mask,start,goal)
            if route:
                length=sum(math.dist(a,b) for a,b in zip(route,route[1:]))
                choices.append((length,d,route))
        if not choices: return None
        _,d,r=min(choices,key=lambda z:z[0]); return d,[(x*s,y*s) for x,y in r]
    def run(self):
        print('F7 start/resume | F6 pause | F8 exit. Keep map and prompt visible.')
        try:
            while True:
                self.interrupt()
                if not self.active:
                    if self.kb.is_pressed('f7'): self.active=True
                    else: time.sleep(.1); continue
                try:
                    p=self.position(); plan=self.plan(p)
                    if not plan: self.release(); self.wait(1); continue
                    door,route=plan; print('Target',door['id'])
                    deadline=time.monotonic()+self.c['route_timeout_s']; previous=p; moved=time.monotonic()
                    knocked=False
                    for target in route[1:]+[route[-1]]:
                        while self.active:
                            if self.interrupt(): break
                            p=self.position()
                            if math.dist(p,previous)>self.c['stuck_distance_px']: previous=p; moved=time.monotonic()
                            if time.monotonic()>deadline or time.monotonic()-moved>self.c['stuck_timeout_s']: raise RuntimeError('Route timed out or character stuck')
                            if math.dist(p,(door['x'],door['y']))<self.c['knock_radius_px'] and self.prompt():
                                self.release()
                                if not self.wait(.15): break
                                if self.prompt():
                                    self.keys.press('e'); knocked=True
                                    self.ledger[str(door['id'])]=time.time()+self.c['cooldown_s']
                                    self.ledger_path.write_text(json.dumps(self.ledger,indent=2))
                                    self.wait(self.c['animation_wait_s'])
                                break
                            if math.dist(p,target)<self.c['waypoint_radius_px']: break
                            self.move(p,target); time.sleep(.08)
                        if knocked or not self.active: break
                    self.release()
                    if self.active and not knocked: raise RuntimeError('Reached approach point but no E prompt; adjust door/approach marker')
                except RuntimeError as e:
                    self.release(); self.active=False; print(e)
        finally: self.release()

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--capture-prompt',action='store_true'); args=parser.parse_args()
    c=json.loads((ROOT/'config.json').read_text())
    if args.capture_prompt:
        import mss
        print('Stand at a door with the E prompt visible. Capturing configured prompt_roi in 5 seconds.'); time.sleep(5)
        x,y,w,h=c['prompt_roi']
        with mss.mss() as sct: im=np.array(sct.grab(dict(left=x,top=y,width=w,height=h)))[:,:,:3]
        cv2.imwrite(str(ROOT/'data/e_prompt.png'),im); print('Saved. Crop to the stable E/key icon before running.')
    else:
        if not c['calibrated']: raise SystemExit('Read README and calibrate config.json; then set calibrated=true.')
        Bot(c).run()
