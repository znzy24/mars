
import network
import socket
import time

from iCenterCar.z_uart import Robot_UART

# WiFi配置
SSID = 'Xiaomi 14 Pro znzy24'
PASSWORD = '30170200'

# 机械臂参数
ARM_SERVO_1 = 21
ARM_SERVO_2 = 22
ARM_SERVO_3 = 23
ARM_SERVO_4 = 24

car_servo_fl_init=1500
car_servo_fr_init=1500
car_servo_bl_init=1500
car_servo_br_init=1500

uart = Robot_UART()
def arm_move_1(arm_id, arm_ang, move_time):
    print("arm_move_1", arm_id, arm_ang, move_time)
    armSrt='#{0:0>3d}P{1:0>4d}T{2:0>4d}!'.format(arm_id,arm_ang,move_time)
    uart.uart_send_str(armSrt)  
    pass

def car_run_and_turn(run_speed, turn_angle, run_time):
    print("car_run_and_turn", run_speed, turn_angle, run_time)
    Srt='#001P{0:0>4d}T{8:0>4d}!#002P{1:0>4d}T{8:0>4d}!#003P{2:0>4d}T{8:0>4d}!#004P{3:0>4d}T{8:0>4d}!#011P{4:0>4d}T{8:0>4d}!#012P{5:0>4d}T{8:0>4d}!#013P{6:0>4d}T{8:0>4d}!#014P{7:0>4d}T{8:0>4d}!'.format(1500-run_speed,1500+run_speed,1500-run_speed,1500+run_speed,1500-turn_angle,1500-turn_angle,1500+turn_angle,1500+turn_angle,run_time)
    uart.uart_send_str(Srt)
    pass

def car_stop():
    print("car_stop()")
    Srt = '#001P1500T1000!#002P1500T1000!#003P1500T1000!#004P1500T1000!#011P{0:0>4d}T1000!#012P{1:0>4d}T1000!#013P{2:0>4d}T1000!#014P{3:0>4d}T1000!'.format(car_servo_fl_init,car_servo_fr_init,car_servo_bl_init,car_servo_br_init)
    uart.uart_send_str(Srt)
    pass

def handle_command(cmd):
    """解析并执行命令，兼容网页按钮和socket指令"""
    cmd = cmd.upper()
    if cmd == 'GROUND' or cmd == 'GRIPPER_GROUND':
        arm_move_1(22, 550, 1000)
        arm_move_1(23, 1620, 1000)
        time.sleep(1)
        arm_move_1(21, 1500, 1000)
    elif cmd == 'CARGO' or cmd == 'GRIPPER_CARGO':
        arm_move_1(22, 1560, 1000)
        arm_move_1(23, 860, 1000)
        time.sleep(1)
        arm_move_1(21, 540, 1000)
    elif cmd == 'FORWARD' or cmd == 'CHASSIS_FORWARD':
        car_run_and_turn(800, 0, 1000)
    elif cmd == 'BACKWARD' or cmd == 'CHASSIS_BACKWARD':
        car_run_and_turn(-800, 0, 1000)
    elif cmd == 'LEFT' or cmd == 'CHASSIS_LEFT':
        car_run_and_turn(0, 200, 1000)
    elif cmd == 'RIGHT' or cmd == 'CHASSIS_RIGHT':
        car_run_and_turn(0, -200, 1000)
    elif cmd == 'STOP' or cmd == 'CHASSIS_RESET':
        car_stop()
    elif cmd == 'ARM1_LEFT':
        arm_move_1(21, 2000, 1000)
    elif cmd == 'ARM1_RIGHT':
        arm_move_1(21, 1000, 1000)
    elif cmd == 'ARM1_RESET':
        arm_move_1(21, 1500, 1000)
    elif cmd == 'ARM2_UP':
        arm_move_1(22, 700, 1000)
    elif cmd == 'ARM2_DOWN':
        arm_move_1(22, 2000, 1000)
    elif cmd == 'ARM2_RESET':
        arm_move_1(22, 1350, 1000)
    elif cmd == 'ARM3_UP':
        arm_move_1(23, 700, 1000)
    elif cmd == 'ARM3_DOWN':
        arm_move_1(23, 2000, 1000)
    elif cmd == 'ARM3_RESET':
        arm_move_1(23, 1000, 1000)
    elif cmd == 'GRIPPER_GRASP':
        arm_move_1(24, 1000, 3)
    elif cmd == 'GRIPPER_RELEASE':
        arm_move_1(24, 2000, 3)
    elif cmd == 'LOADER_UNLOAD':
        print('Loader unload')
    elif cmd == 'LOADER_RESET':
        print('Loader reset')
    else:
        print('Unknown command:', cmd)
# ====== MicroPython HTTP Web Server ======
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print('Network config:', wlan.ifconfig())

def main():
    connect_wifi()
    # 读取 code.html
    try:
        with open('/iCenterCar/code.html', 'r', encoding='utf-8') as f:
            html = f.read()
    except:
        html = '<h1>code.html not found</h1>'

    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('listening on', addr)

    while True:
        cl, addr = s.accept()
        print('client connected from', addr)
        try:
            request = cl.recv(1024)
            req = request.decode('utf-8')
            if 'GET / ' in req or 'GET /code.html' in req:
                response = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n' + html
                cl.send(response.encode('utf-8'))
            elif 'GET /cmd?' in req:
                # 例如 GET /cmd?cmd=chassis_forward
                cmd = req.split('cmd=')[-1].split(' ')[0]
                handle_command(cmd)
                cl.send('HTTP/1.1 200 OK\r\n\r\nOK'.encode())
            else:
                cl.send('HTTP/1.1 404 Not Found\r\n\r\n'.encode())
        except Exception as e:
            print('Error:', e)
        cl.close()

if __name__ == '__main__':
    main()

