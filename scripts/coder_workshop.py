#!/usr/bin/env python3
"""Render a looping, button-free 3D coder scene for a GitHub README.

The supplied Three.js factory inspired the graphite platform, orange accents,
and workshop lighting. This scene is rendered offline so GitHub can display it
as an animated image. Requires numpy and Pillow; no models or remote assets.
"""

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
W, H, AA = 1000, 640, 2
FORWARD = np.array([.64, 0, -.77])
RIGHT = np.array([.77, 0, .64])
UP = np.array([0., 1., 0.])
EYE = np.array([9., 8., 11.]); EYE /= np.linalg.norm(EYE)
CAM_RIGHT = np.cross(UP, EYE); CAM_RIGHT /= np.linalg.norm(CAM_RIGHT)
CAM_UP = np.cross(EYE, CAM_RIGHT)
LIGHT = np.array([-3., 8., 6.]); LIGHT /= np.linalg.norm(LIGHT)
TARGET = np.array([0., 1.85, 0.])
SCALE = 84
COLORS = {
    "steel": "#59616b", "dark": "#171d25", "edge": "#77818e",
    "orange": "#e87529", "skin": "#dbab82", "hair": "#25202a",
    "screen": "#111922", "ivory": "#d7dedb", "green": "#74c6a2",
}


def project(points):
    points = np.asarray(points)-TARGET
    return np.column_stack((W/2 + points @ CAM_RIGHT * SCALE, H*.415 - points @ CAM_UP * SCALE))


def rgb(color):
    if color in COLORS: color = COLORS[color]
    return np.array([int(color[i:i+2], 16) for i in (1, 3, 5)])


class Scene:
    def __init__(self): self.faces = []

    def face(self, points, color, glow=False):
        points = np.asarray(points, dtype=float)
        normal = np.cross(points[1]-points[0], points[2]-points[0])
        length = np.linalg.norm(normal)
        if length < 1e-7: return
        normal /= length
        if normal @ EYE < -.01: return
        strength = 1 if glow else .40 + .56*max(0, normal @ LIGHT) + .13*max(0, normal[1])
        shade = np.clip(rgb(color)*strength + (np.array([7, 9, 13]) if not glow else 0), 0, 255).astype(int)
        self.faces.append((float(points.mean(axis=0) @ EYE), points, tuple(shade)))

    def box(self, center, size, color, axes=None, glow=False):
        center = np.array(center); axes = np.eye(3) if axes is None else np.array(axes).T
        vertices = [center+axes @ (np.array([x,y,z])*np.array(size)/2)
                    for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        for indices in [(0,3,2,1),(4,5,6,7),(0,4,7,3),(1,2,6,5),(3,7,6,2),(0,1,5,4)]:
            self.face([vertices[i] for i in indices], color, glow)

    def sphere(self, center, radius, color, scale=(1,1,1), rings=10, segments=18, cap=math.pi):
        center=np.array(center);factor=np.array(scale)*radius
        def point(theta, phi): return center+factor*np.array([math.sin(theta)*math.cos(phi),math.cos(theta),math.sin(theta)*math.sin(phi)])
        for j in range(rings):
            a,b=j*cap/rings,(j+1)*cap/rings
            for i in range(segments):
                p,q=i*math.tau/segments,(i+1)*math.tau/segments
                self.face([point(a,q),point(b,q),point(b,p),point(a,p)],color)

    def rod(self, a, b, radius, color, segments=12, end_radius=None):
        a,b=np.array(a),np.array(b);axis=b-a;axis/=np.linalg.norm(axis)
        u=np.cross(axis,[0,1,0] if abs(axis[1])<.95 else [1,0,0]);u/=np.linalg.norm(u)
        v=np.cross(axis,u);r2=radius if end_radius is None else end_radius
        pa=[a+radius*(u*math.cos(i*math.tau/segments)+v*math.sin(i*math.tau/segments)) for i in range(segments)]
        pb=[b+r2*(u*math.cos(i*math.tau/segments)+v*math.sin(i*math.tau/segments)) for i in range(segments)]
        for i in range(segments):
            j=(i+1)%segments
            self.face([pa[j],pb[j],pb[i],pa[i]],color)
        self.face(pa[::-1],color);self.face(pb,color)


def scene_at(t):
    s=Scene();phase=t*math.tau/6
    # A machined base with two narrow amber inlays and corner fasteners.
    s.box((0,-.16,0),(7.7,.32,5.9),"dark")
    s.box((0,.015,0),(7.45,.06,5.65),"steel")
    for x in [-3.5,3.5]:
        s.box((x,.055,0),(.035,.014,5.2),"orange",glow=True)
        for z in [-2.5,2.5]:s.rod((x,.06,z),(x,.085,z),.07,"edge")
    # Desk, metal frame, cross-brace and a warm wood/graphite work surface.
    for x in [-2.1,2.5]:
        for z in [-1.1,1.0]:s.box((x,1.02,z),(.14,1.98,.14),"dark")
        s.rod((x,.30,-1.1),(x,1.85,1.0),.025,"steel")
    s.box((.2,2.1,-.05),(5.0,.16,2.65),"dark")
    s.box((.2,2.195,-.05),(5.08,.045,2.70),"#67605b")
    s.box((.2,2.205,1.29),(5.08,.025,.026),"orange",glow=True)
    # Main monitor: a physical bezel, editor rail and growing syntax lines.
    s.box((.75,2.27,-.68),(.84,.06,.55),"dark")
    s.rod((.75,2.3,-.68),(.75,2.86,-.68),.075,"steel")
    s.box((.75,3.42,-.68),(2.66,1.7,.17),"dark")
    s.box((.75,3.42,-.581),(2.44,1.48,.014),"screen",glow=True)
    s.box((.75,4.115,-.565),(2.36,.027,.007),"orange",glow=True)
    for j,col in enumerate(["#e97b57","#d9b26b","#74c6a2"]):
        s.sphere((-.36+j*.095,4.075,-.55),.023,col,rings=5,segments=8)
    for j in range(9):
        y=3.96-j*.135
        s.box((-.33,y,-.553),(.045,.018,.006),"#63707e",glow=True)
        indent=.17 if j in [2,3,5,6] else 0
        full=[1.3,.92,1.6,1.03,.76,1.5,.93,1.42,.58][j]
        progress=np.clip((t%6)*2.2-j+.8, .03,1)
        length=full*progress
        col=["#bd9ce7","#78b7cd","#e9af74","#9acdae"][j%4]
        s.box((-.15+indent+length/2,y,-.55),(length,.035,.007),col,glow=True)
    cursor_line=min(8,int((t%6)*2.2))
    cursor_y=3.96-cursor_line*.135
    if int(t*3)%2==0:s.box((.22,cursor_y,-.541),(.022,.08,.008),"ivory",glow=True)
    # A portrait terminal screen to the left and a small speaker to the right.
    s.box((-1.40,2.27,-.73),(.6,.05,.5),"dark")
    s.rod((-1.40,2.3,-.73),(-1.40,2.87,-.73),.055,"steel")
    s.box((-1.40,3.37,-.73),(1.02,1.56,.16),"dark")
    s.box((-1.40,3.37,-.637),(.85,1.37,.01),"screen",glow=True)
    for j in range(9):
        s.box((-1.70+(.25+.035*j)/2,3.91-j*.11,-.626),(.25+.035*j,.018,.005),"#6c9c89",glow=True)
    s.box((-1.40,2.85,-.624),(.68,.055,.006),"#294e40",glow=True)
    s.box((-1.74+(.68*(t%6)/6)/2,2.85,-.614),(.68*(t%6)/6+.01,.055,.008),"green",glow=True)
    s.box((2.23,2.51,-.8),(.30,.61,.34),"dark")
    for y,r in [(2.6,.088),(2.38,.056)]:s.sphere((2.23,y,-.619),r,"steel",scale=(1,1,.16),rings=6,segments=10)
    # Keyboard and mouse, with a row of gently flashing amber keys.
    s.box((-.05,2.25,.73),(1.57,.07,.56),"dark")
    for row in range(4):
        for col in range(13):
            color="orange" if col==(int(t*12)+row*2)%13 else "#8b939a"
            s.box((-.76+col*.117,2.30,.53+row*.126),(.082,.025,.085),color)
    s.box((-.05,2.30,.965),(.66,.027,.075),"steel")
    s.box((1.15,2.23,.83),(.64,.012,.69),"#2a3038")
    s.sphere((1.18,2.30,.83),.13,"ivory",scale=(.68,.40,1.2),rings=7,segments=12)
    # Coffee, books, a softly lit desktop tower, and a small plant.
    s.rod((1.93,2.22,.44),(1.93,2.54,.44),.14,"ivory")
    s.rod((1.93,2.542,.44),(1.93,2.547,.44),.115,"#4d3023")
    s.rod((2.12,2.32,.44),(2.12,2.44,.44),.032,"ivory")
    s.rod((2.00,2.46,.44),(2.12,2.44,.44),.032,"ivory")
    s.rod((2.00,2.3,.44),(2.12,2.32,.44),.032,"ivory")
    for j,col in enumerate(["#626d7d","#dd813a","#b4b7af"]):
        s.box((2.12,2.24+j*.075,-.04),(.62,.066,.40),col)
    s.box((2.68,.66,.32),(.62,1.30,1.13),"dark")
    s.box((3.003,.77,.39),(.014,.68,.75),"steel")
    for z in [.18,.57]:
        s.sphere((3.014,.88,z),.14,"#306057",scale=(.12,1,1),rings=8,segments=14)
        s.sphere((3.038,.88,z),.045,"green",scale=(.2,1,1),rings=6,segments=10)
    s.box((2.68,1.25,.87),(.25,.017,.02),"orange",glow=True)
    px,pz=-3.03,.35
    s.rod((px,.06,pz),(px,.52,pz),.34,"#887b6d",end_radius=.27)
    for j in range(9):
        angle=j*2.4;top=np.array([px+math.cos(angle)*.25,.75+j*.055,pz+math.sin(angle)*.25])
        s.rod((px,.51,pz),top,.015,"#477361")
        s.sphere(top,.19,"#579175",scale=(.38,1.5,.45),rings=6,segments=9)
    # A seated coder. Local axes keep the posture aimed at the workstation.
    body=np.array([-.9,2.15,1.75]);axes=[RIGHT,UP,FORWARD]
    def local(r,y,f):return body+RIGHT*r+UP*y+FORWARD*f
    seat=local(0,-.20,-.05)
    s.box(seat,(.83,.16,.79),"dark",axes)
    s.box(local(0,.37,-.45),(.88,1.19,.14),"#383d48",axes)
    s.box(local(0,.38,-.532),(.77,.95,.014),"#7a4d35",axes)
    s.rod((seat[0],.37,seat[2]),seat,.075,"steel")
    for j in range(5):
        a=j*math.tau/5;end=np.array([seat[0]+.65*math.cos(a),.13,seat[2]+.65*math.sin(a)])
        s.rod((seat[0],.36,seat[2]),end,.045,"steel")
        s.sphere(end,.10,"dark",scale=(1,.65,1),rings=6,segments=10)
    for sign in [-1,1]:
        hip=local(sign*.19,-.15,.08);knee=local(sign*.22,-.70,.65);foot=local(sign*.22,-1.85,.78)
        s.rod(hip,knee,.16,"#303a4d",end_radius=.14)
        s.rod(knee,foot+UP*.20,.12,"#303a4d")
        s.sphere(foot,.23,"ivory",scale=(.69,.35,1.3),rings=7,segments=12)
    s.rod(local(0,-.04,0),local(0,.87,0),.37,"orange",end_radius=.29,segments=20)
    s.sphere(local(0,.90,-.09),.30,"#b45f2b",scale=(1,.60,1.10),rings=8,segments=15)
    # Head tilt, blinking eyes and a hairstyle make the coder feel alive.
    head=local(0,1.38+.025*math.sin(phase*2),.08)
    face_dir=FORWARD+RIGHT*.18;face_dir/=np.linalg.norm(face_dir)
    s.sphere(head,.37,"skin",scale=(.92,1.09,.96),rings=13,segments=22)
    s.sphere(head+UP*.08-face_dir*.05,.385,"hair",rings=8,segments=22,cap=math.pi*.55)
    for sign in [-1,1]:
        s.sphere(head+RIGHT*sign*.33,.077,"skin",scale=(.6,1,.7),rings=7,segments=10)
        eye=head+face_dir*.345+RIGHT*sign*.122+UP*.015
        blink=.13 if 2.67<t%6<2.86 else 1
        s.sphere(eye,.030,"hair",scale=(1,blink,1),rings=6,segments=10)
        s.rod(eye+UP*.065-RIGHT*.042,eye+UP*.072+RIGHT*.042,.012,"hair",segments=7)
    s.sphere(head+face_dir*.373-UP*.055,.058,"skin",rings=7,segments=10)
    s.rod(head+face_dir*.348-UP*.145-RIGHT*.044,head+face_dir*.348-UP*.145+RIGHT*.044,.012,"#965f49",segments=7)
    # Alternating keystrokes; briefly move the right hand to the mouse.
    for sign in [-1,1]:
        shoulder=local(sign*.30,.75,.035)
        elbow=local(sign*.35,.25,.43)
        wrist=np.array([-.34+sign*.25,2.39+.025*math.sin(t*math.tau*3+sign),.80])
        if sign==1:
            mouse_mix=max(0,math.sin((t-3)*math.pi/1.7)) if 3<t<4.7 else 0
            wrist=wrist*(1-mouse_mix)+np.array([1.12,2.36,.83])*mouse_mix
            elbow=elbow*(1-mouse_mix*.35)+np.array([.55,2.66,1.0])*mouse_mix*.35
        s.rod(shoulder,elbow,.13,"orange",end_radius=.105)
        s.sphere(elbow,.107,"orange",rings=7,segments=11)
        s.rod(elbow,wrist,.095,"orange",end_radius=.071)
        s.sphere(wrist+FORWARD*.055,.10,"skin",scale=(1,.55,1.15),rings=7,segments=12)
    return s


def backdrop():
    yy,xx=np.mgrid[0:H*AA,0:W*AA]
    glow=np.exp(-(((xx-W*AA*.48)/(W*AA*.40))**2+((yy-H*AA*.47)/(H*AA*.46))**2)*2)
    colors=np.stack((12+18*glow,16+15*glow,22+15*glow),axis=-1).astype('uint8')
    img=Image.fromarray(colors,"RGB")
    shadow=Image.new("RGBA",img.size);d=ImageDraw.Draw(shadow)
    d.ellipse((110*AA,340*AA,890*AA,612*AA),fill=(0,0,0,190))
    img=Image.alpha_composite(img.convert('RGBA'),shadow.filter(ImageFilter.GaussianBlur(24*AA))).convert('RGB')
    return img


def frame(t, background):
    image=background.copy();draw=ImageDraw.Draw(image)
    for _,points,color in sorted(scene_at(t).faces,key=lambda f:f[0]):
        projected=project(points)*AA
        draw.polygon([tuple(p) for p in projected],fill=color)
    steam=Image.new('RGBA',image.size);mist=ImageDraw.Draw(steam)
    for j in range(3):
        rise=(t/2+j/3)%1
        points=[(1.93+.045*math.sin(t*math.pi+j+k*.5),2.58+rise*.42+k*.045,.44) for k in range(6)]
        mist.line([tuple(p) for p in project(points)*AA],fill=(178,185,194,int(65*(1-rise))),width=2*AA)
    image=Image.alpha_composite(image.convert('RGBA'),steam.filter(ImageFilter.GaussianBlur(AA))).convert('RGB')
    return image.resize((W,H),Image.Resampling.LANCZOS)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview',type=Path)
    args=parser.parse_args();background=backdrop()
    if args.preview:
        frame(.55,background).save(args.preview)
        print(f'Saved preview: {args.preview}',flush=True);return
    frames=[]
    for i in range(120):
        frames.append(frame(i/20,background))
        if i%20==0:print(f'Rendered {i}/120 frames',flush=True)
    # A shared palette avoids color flicker across frames.
    atlas=Image.new('RGB',(W, H*6))
    for j,i in enumerate(range(0,120,20)):atlas.paste(frames[i],(0,j*H))
    palette=atlas.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    output=ROOT/'assets/coder-workshop.gif'
    indexed[0].save(output,save_all=True,append_images=indexed[1:],duration=50,loop=0,optimize=True,disposal=1)
    frames[11].save(ROOT/'assets/coder-workshop.png',optimize=True)
    print(f'Saved {output}: {output.stat().st_size:,} bytes, 120 frames, 6-second loop',flush=True)


if __name__=='__main__':main()
