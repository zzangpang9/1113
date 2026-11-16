"""bichon.py - 비숑이 뛰어가며 줌 아웃되는 ASCII 애니메이션

실행: python3 bichon.py        (터미널 크기 90열 x 38행 이상 권장)
종료: Ctrl+C
"""
import math
import sys
import time

W, H = 90, 36          # 화면 격자 크기
FPS = 30
HORIZON = -32          # 지평선 높이 (월드 좌표, 위쪽이 음수)
DURATION = 14.0        # 한 번 재생 시간(초)
ZOOM_TIME = 10.0       # 줌 아웃에 걸리는 시간(초)
Z0, Z1 = 2.2, 0.75      # 시작/끝 배율
CAM_Y_END = -14.0      # 줌 아웃 끝에서 카메라가 올라가는 높이
SPEED = 30.0           # 비숑이 달리는 속도 (월드 단위/초)

SKY = [153, 117, 81, 75, 39, 33]       # 지평선 → 높은 하늘
GROUND = [71, 70, 34, 28, 22]          # 먼 들판 → 가까운 들판

CLOUDS = [(20, -48, 14, 4), (27, -52, 9, 4), (70, -62, 16, 4.5),
          (78, -66, 9, 4), (100, -44, 12, 3.5)]


def smooth(a):
    a = max(0.0, min(1.0, a))
    return a * a * (3 - 2 * a)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def ell(x, y, cx, cy, rx, ry, phase=0.0):
    """타원 내부 값(1 이하면 내부). 가장자리를 살짝 일렁이게 해 털 느낌을 낸다."""
    dx, dy = x - cx, y - cy
    v = (dx / rx) ** 2 + (dy / ry) ** 2
    ang = math.atan2(dy, dx)
    return v * (1 + 0.10 * math.sin(7 * ang + phase))


def dog_pixel(lx, ly, ph):
    """비숑 로컬 좌표(오른쪽을 보고 달림). (문자, 글자색, 배경색) 또는 None."""
    # 눈·코 (검정)
    if ell(lx, ly, 17.0, -11.0, 1.4, 1.2) < 1:
        return ('o', 16, 16)
    if ell(lx, ly, 25.0, -8.0, 2.0, 1.6) < 1:
        return ('@', 16, 16)

    f = 0.6 * ph
    # 앞 귀(가장 앞), 다리, 몸통 순서로 겹쳐 그린다
    v = ell(lx, ly, 12.5, -4.5, 3.4, 7.0, f)
    if v < 1:
        return (_fur(lx, ly), 244 if v > 0.55 else 247, 252)

    for hx, off in ((10, 0.0), (6, 0.7), (-7, math.pi), (-11, math.pi + 0.7)):
        p = ph + off
        fx = hx + 9 * math.sin(p)
        fy = 16 - max(0.0, math.cos(p)) * 5
        d = seg_dist(lx, ly, hx, 5, fx, fy)
        if d < 3.2:
            return (_fur(lx, ly), 244 if d > 2.2 else 250, 253)

    parts = (
        (17, -9.5, 7.8, 7.8),    # 머리
        (24, -7.0, 4.2, 3.4),    # 주둥이
        (-14, -10, 5.0, 5.0),    # 꼬리
        (0, 0, 14, 8.5),         # 몸통
    )
    for cx, cy, rx, ry in parts:
        v = ell(lx, ly, cx, cy, rx, ry, f)
        if v < 1:
            return (_fur(lx, ly), 244 if v > 0.62 else 250, 255)
    return None


_FUR = '@&%8#'


def _fur(x, y):
    return _FUR[(int(x * 3.1) ^ int(y * 5.7)) % len(_FUR)]


def render(t):
    prog = smooth(t / ZOOM_TIME)
    z = Z0 + (Z1 - Z0) * prog
    cam_y = CAM_Y_END * prog
    dog_x = SPEED * t
    cam_x = dog_x + 6                       # 비숑이 화면 왼쪽에 오도록
    ph = t * 2 * math.pi * 2.6              # 달리기 주기
    bounce = -abs(math.sin(ph)) * 3.0       # 뛸 때 위아래 출렁임

    rows = []
    for cy in range(H):
        row = []
        wy = cam_y + (cy - H / 2) * 2 / z
        for cx in range(W):
            wx = cam_x + (cx - W / 2) / z
            ch, fg, bg = ' ', 15, 33

            if wy < HORIZON:                                   # 하늘
                k = min(1.0, (HORIZON - wy) / 55) * (len(SKY) - 1)
                bg = SKY[int(k)]
                sx = (wx - cam_x * 0.9) % 120
                for ccx, ccy, rx, ry in CLOUDS:
                    if ell(sx, wy, ccx, ccy, rx, ry) < 1:
                        bg = 255 if wy > ccy else 254
                        break
            else:                                              # 들판
                d = wy - HORIZON
                bg = GROUND[min(len(GROUND) - 1, int(d / 22))]
                gx, gy = math.floor(wx / 5), math.floor(wy / 3)
                hsh = ((gx * 73856093) ^ (gy * 19349663)) & 0xFFFF
                if hsh % 151 == 0:
                    ch, fg = '*', (226 if hsh % 2 else 213)
                elif hsh % 4 == 0:
                    ch, fg = '"\'`|/,'[hsh % 6], 112
                # 그림자
                if ell(wx - dog_x, wy, 2, 17, 17, 2.5) < 1:
                    bg, ch = 22, ' '

            px = dog_pixel(wx - dog_x, wy - bounce, ph)
            if px:
                ch, fg, bg = px
            row.append((ch, fg, bg))
        rows.append(row)
    return rows


def to_ansi(rows, status):
    out = ['\033[H']
    for row in rows:
        last = None
        for ch, fg, bg in row:
            if (fg, bg) != last:
                out.append(f'\033[38;5;{fg};48;5;{bg}m')
                last = (fg, bg)
            out.append(ch)
        out.append('\033[0m\n')
    out.append(status + '\033[K')
    return ''.join(out)


def main():
    sys.stdout.write('\033[?25l\033[2J')
    try:
        start = time.time()
        while True:
            t = (time.time() - start) % DURATION
            z = Z0 + (Z1 - Z0) * smooth(t / ZOOM_TIME)
            status = f'bichon.py  running · {FPS} fps · zoom x{z:.2f}'
            sys.stdout.write(to_ansi(render(t), status))
            sys.stdout.flush()
            time.sleep(1 / FPS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\033[0m\033[?25h\n')


if __name__ == '__main__':
    main()
