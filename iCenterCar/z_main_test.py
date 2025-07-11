'''
编写信息
作者：郑养波
日期：2025年6月1日
函数框架说明：

函数变量说明：
函数变量说明：
1. 底盘电机ID可用范围:001-010 本次用4个
001---car_motor_fl---左前轮
002---car_motor_fr---右前轮
003---car_motor_bl---左后轮
004---car_motor_br---右后轮
2. 地盘舵机ID:011-020 本次用4个
011---car_servo_fl---左前轮
012---car_servo_fr---右前轮
013---car_servo_bl---左后轮
014---car_servo_br---右后轮
3. 机械臂舵机ID:021-030 其中，个数学生自己选择 可以增加运动学
021---arm_servo_1---机械臂1号舵机 自下而上
022---arm_servo_2---机械臂2号舵机
023---arm_servo_3---机械臂3号舵机
024---arm_servo_4---机械臂4号舵机
……
'''

#一、库文件导入
import re							#正则表达式模块，用于字符串匹配和处理
import time
import _thread
# 从`factory`包中导入各种自定义模块，分别用于控制LED、蜂鸣器、按键、ADC、串口、文件、舵机、运动学和PS2手柄
from iCenterCar.z_led import Mars_LED
from iCenterCar.z_beep import Mars_BEEP
from iCenterCar.z_key import Mars_KEY
from iCenterCar.z_uart import Mars_UART
from iCenterCar.z_ps2 import Mars_PS2


#二、全局变量定义
#2.1 定义总线设备ID号
car_motor_fl=001                #小车左前轮电机ID
car_motor_fr=002                #小车右前轮电机ID
car_motor_bl=003                #小车左后轮电机ID
car_motor_br=004                #小车右后轮电机ID

car_servo_fl=011                #小车左前轮舵机ID   
car_servo_fr=012                #小车右前轮舵机ID   
car_servo_bl=013                #小车左后轮舵机ID   
car_servo_br=014                #小车右后轮舵机ID

arm_servo_1=021                 #机械臂第1个舵机ID       
arm_servo_2=022                 #机械臂第2个舵机ID
arm_servo_3=023                 #机械臂第3个舵机ID
arm_servo_4=024                 #机械臂第4个舵机ID

#2.2定义底盘转向舵机的初始位置PWM数值，并将测试得到数值对以下数值进行更新
car_servo_fl_init=1500
car_servo_fr_init=1500
car_servo_bl_init=1500
car_servo_br_init=1500

#2.3定义机械臂舵机的初始位置PWM数值，并将测试得到数值对以下数值进行更新
arm_servo_1_init=1500
arm_servo_2_init=1350
arm_servo_3_init=1500
arm_servo_4_init=1500

#2.4定义机械臂舵机的实时PWM数值，初始数值为init,后面根据控制情况实时调整
arm_servo_1_pwm=arm_servo_1_init
arm_servo_2_pwm=arm_servo_2_init
arm_servo_3_pwm=arm_servo_3_init
arm_servo_4_pwm=arm_servo_4_init
#定义机械臂运动的时间
arm_move_time = 2000					#机械臂运动时间，单位ms

#2.5 定义车速
car_run_speed= 800   				#小车直行运动速度，范围0~1000us 此数值是PWM输出数值，范围为500us-2500us之间，其中1500us电机停止，大于1500us正转，小于1500us反转
car_run_time = 5000					#小车直行时间1000=1s	该数值用于启动车子的运动

#小车转弯参数
car_turn_speed = 400					#小车转弯时的速度
car_turn_angle = 200 					#小车转弯角度，范围0~1000
car_turn_time = 8000					#小车转弯时间，暂时赋值

#2.6定义手柄控制参数
#ps2_systick_ms = 0                      #记录手柄历史时间戳
ps2_arm_inc= 100						#手柄遥控的每一次增量 机械臂的舵机增量-PWM数值

#2.3机械臂参数
car_turn_arm1=0						#转弯舵机1初始值，默认是PWM是1500
car_turn_arm2=0						#转弯舵机1初始值，默认是PWM是1500
car_turn_arm3=0						#转弯舵机1初始值，默认是PWM是1500
car_turn_arm4=0						#转弯舵机1初始值，默认是PWM是1500


#2.4 根据推进的遥感模拟量来计算车速 取最小值
speed_pwm=0					            #通过遥感计算得到的速度

#2.5标志位定义
voice_flag = 0					    #语音控制开关标记  1-开启；0-关闭
car_move_tag=0					    #底盘运动控制标记，1-说明运动要变化，0-说明运动不变化
arm_move_tag=0					    #机械臂运动控制标记，1-说明运动要变化，0-说明运动不变化


#三、函数定义
#3.1 定义时间函数
def millis():
    return int(time.time_ns()//1000000)

#3.2 定义传感器的模式
def loop_sensor():
    return

#3.3 LED灯处理函数-循环控制
def loop_nled():
    nled.loop_nled()                           # led灯循环亮灭

#3.4 定义小车运动函数
#3.4.1 定义底盘舵机初始化函数，即再一次对中位值进行校准
def car_servos_init():
    Srt = '#011P{0:0>4d}T{4:0>4d}!#012P{1:0>4d}T{4:0>4d}!#013P{2:0>4d}T{4:0>4d}!#014P{3:0>4d}T{4:0>4d}!'.format(car_servo_fl_init,car_servo_fr_init,car_servo_bl_init,car_servo_br_init,1000)
    print(Srt)
    print("Car servos are tunning")
    uart.uart_send_str(Srt)
#3.4.2 小车直行运动函数
def car_run(run_speed,run_time):
    Srt = '#001P{0:0>4d}T{4:0>4d}!#002P{1:0>4d}T{4:0>4d}!#003P{2:0>4d}T{4:0>4d}!#004P{3:0>4d}T{4:0>4d}!'.format(1500-run_speed,1500+run_speed,1500-run_speed,1500+run_speed,run_time)
    print(Srt)
    print("Car is running")
    uart.uart_send_str(Srt)
        
#3.4.3 定义小车转弯运动
def car_turn(turn_angle,turn_time):
    Srt='#011P{0:0>4d}T{4:0>4d}!#012P{1:0>4d}T{4:0>4d}!#013P{2:0>4d}T{4:0>4d}!#014P{3:0>4d}T{4:0>4d}!'.format(1500-turn_angle,1500-turn_angle,1500+turn_angle,1500+turn_angle,turn_time)
    print(Srt)
    print("Car is turning")
    uart.uart_send_str(Srt)
        
#3.4.4 小车运动+转向
def car_run_and_turn(run_speed,turn_angle,run_time):
    Srt='#001P{0:0>4d}T{8:0>4d}!#002P{1:0>4d}T{8:0>4d}!#003P{2:0>4d}T{8:0>4d}!#004P{3:0>4d}T{8:0>4d}!#011P{4:0>4d}T{8:0>4d}!#012P{5:0>4d}T{8:0>4d}!#013P{6:0>4d}T{8:0>4d}!#014P{7:0>4d}T{8:0>4d}!'.format(1500-run_speed,1500+run_speed,1500-run_speed,1500+run_speed,1500-turn_angle,1500-turn_angle,1500+turn_angle,1500+turn_angle,run_time)
    print(Srt)
    print("Car is running and turning")
    uart.uart_send_str(Srt)
    
#3.4.5小车停止函数 #停止车轮和转向
def car_stop():
    Srt = '#001P1500T1000!#002P1500T1000!#003P1500T1000!#004P1500T1000!#011P{0:0>4d}T1000!#012P{1:0>4d}T1000!#013P{2:0>4d}T1000!#014P{3:0>4d}T1000!'.format(car_servo_fl_init,car_servo_fr_init,car_servo_bl_init,car_servo_br_init)
    print(Srt)
    print("Car is stopping")
    uart.uart_send_str(Srt)

#3.5 定义机械臂运动函数
#3.5.1 定义机械臂舵机初始化函数，即再一次对中
def arm_servos_init():
    Srt = '#021P{0:0>4d}T{4:0>4d}!#022P{1:0>4d}T{4:0>4d}!#023P{2:0>4d}T{4:0>4d}!#024P{3:0>4d}T{4:0>4d}!'.format(arm_servo_1_init,arm_servo_2_init,arm_servo_3_init,arm_servo_4_init,1000)
    print(Srt)
    print("Arm servos are tunning")
    uart.uart_send_str(Srt)
#2. 定义机械臂运动——任何1个关节运动，需要传递arm_id,arm_ang,move_time
def arm_move_1(arm_id,arm_ang,move_time):
    armSrt='#{0:0>3d}P{1:0>4d}T{2:0>4d}!'.format(arm_id,arm_ang,move_time)
    print(armSrt)
    print(arm_id,"is running")
    uart.uart_send_str(armSrt)    

#3.5.2定义机械臂运动——4个关节的运动， 需要传递arm_ang1,arm_ang2,arm_ang3,arm_ang4,move_time
def arm_move_4(arm_ang1,arm_ang2,arm_ang3,arm_ang4,move_time):
    armSrt='#021P{0:0>4d}T{4:0>4d}!#022P{1:0>4d}T{4:0>4d}!#023P{2:0>4d}T{4:0>4d}!#024P{3:0>4d}T{4:0>4d}!'.format(arm_ang1,arm_ang2,arm_ang3,arm_ang4,move_time)
    print(armSrt)
    print("Arm is running")
    uart.uart_send_str(armSrt)
    
#3.5.2定停止运动——4个关节的运动
def arm_stop():
    armSrt='#021P{0:0>4d}T{4:0>4d}!#022P{1:0>4d}T{4:0>4d}!#023P{2:0>4d}T{4:0>4d}!#024P{3:0>4d}T{4:0>4d}!'.format(arm_servo_1_init,arm_servo_2_init,arm_servo_3_init,arm_servo_4_init,1000)
    print(armSrt)
    print("Arm is running")
    uart.uart_send_str(armSrt)


#3.6主函数启动 车子机械臂初始化运动
def car_arm_initial():
     
    #初始化底盘舵机和机械臂舵机，使其位于目标中的初始位置
    car_servos_init()
    time.sleep(1)
    arm_servos_init()
    time.sleep(1)
    
    #直行前进运动测试
    car_run(int(car_run_speed/2),int(car_run_time/2)) #测试阶段速度 时间减半
    time.sleep(1)
    car_stop()
    time.sleep(1) 

    car_run(-int(car_run_speed/2),int(car_run_time/2)) #测试阶段速度 时间减半
    time.sleep(1)
    car_stop()
    time.sleep(1) 

    #转向测试
    car_turn(car_turn_angle,car_turn_time)
    time.sleep(1)
    car_stop()
    time.sleep(1) 

    car_turn(-car_turn_angle,car_turn_time)
    time.sleep(1)
    car_stop()
    time.sleep(1) 

    #转向运动测试
    car_run_and_turn(car_run_speed,car_turn_angle,car_turn_time)
    time.sleep(1)
    car_stop()
    time.sleep(1) 

    car_run_and_turn(-car_run_speed,-car_turn_angle,car_turn_time)
    time.sleep(1)
    car_stop()
    time.sleep(1) 
    
    arm_move_1(arm_servo_1,2000,1000)  #机械臂1号舵机运动
    time.sleep(1)
    
    arm_move_1(arm_servo_1,1000,1000)  #机械臂1号舵机运动
    time.sleep(1)
    
    arm_move_1(arm_servo_1,arm_servo_1_init,1000)  #机械臂1号舵机运动
    time.sleep(1)

    
    #机械臂2号舵机先转到2000，再转到1000，最后回到初始位置
    arm_move_1(arm_servo_2,2000,1000)  #机械臂1号舵机运动
    time.sleep(1)
    
    arm_move_1(arm_servo_2,1000,1000)  #机械臂1号舵机运动
    time.sleep(1)

    arm_move_1(arm_servo_2,arm_servo_2_init,1000)  #机械臂1号舵机运动
    time.sleep(1)
       
    #机械臂3号舵机先转到2000，再转到1000，最后回到初始位置
    arm_move_1(arm_servo_3,2000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_3,1000,1000)  #机械臂1号舵机运动
    time.sleep(2)

    arm_move_1(arm_servo_3,arm_servo_3_init,1000)  #机械臂1号舵机运动
    time.sleep(1)
       
    #机械臂4号舵机先转到2000，再转到1000，最后回到初始位置
    arm_move_1(arm_servo_4,2000,1000)  #机械臂1号舵机运动
    time.sleep(2)
    
    arm_move_1(arm_servo_4,1000,1000)  #机械臂1号舵机运动
    time.sleep(2)

    arm_move_1(arm_servo_4,arm_servo_4_init,1000)  #机械臂1号舵机运动
    time.sleep(1)

    #机械臂的4个舵机同时测试
    #…………
    #初始化车子和机械臂，为开始工作做准备
    car_servos_init()
    time.sleep(1)
    arm_servos_init()
    time.sleep(1)

# ====== 花式轮子全局变量和函数，建议放在主函数定义区前面 ======
fancy_mode = False  # 全局变量，建议放在全局变量区

def fancy_wheel_action(angle=300, time_ms=1000):
    Srt = '#001P{0:0>4d}T{4:0>4d}!#002P{1:0>4d}T{4:0>4d}!#003P{2:0>4d}T{4:0>4d}!#004P{3:0>4d}T{4:0>4d}!'.format(
        1500+angle, 1500-angle, 1500-angle, 1500+angle, time_ms)
    print("花式轮子动作:", Srt)
    uart.uart_send_str(Srt)
# ====== 花式轮子全局变量和函数结束 ======

#3.3处理串口接收的数据
'''
    - 调用uart.recv_str()接收数据
    - 根据接收完成标志（uart.uart_get_ok）判断数据类型：
    '<': '>',   # Type1: <...> 格式
    '{': '}',   # Type2: {...} 格式
    '#': '!',   # Type3: #...! 格式 #动作模式
    '$': '!'    # Type4: $...! 格式 #指令模式
'''
def loop_uart():
    global uart
    uart.recv_str()                           # 串口接收并根据格式处理数据
#     print(uart.uart_receive_str)
   
    #类似$111！
    if uart.uart_get_ok == 4:
#         print("uart.uart_get_ok=",uart.uart_get_ok)
        uart_data_handle(uart.uart_receive_str)         # 处理接收的数据-语音控制
#         uart.uart_receive_str = ''
#         uart.uart_get_ok = 0
#         #指令模式
#     elif uart.uart_get_ok == 1 or uart.uart_get_ok == 2 or uart.uart_get_ok == 3:
# #         print("uart.uart_get_ok=",uart.uart_get_ok)
#         uart.uart_receive_str = ''
#         uart.uart_get_ok = 0
#     else:
# #         print("uart.uart_get_ok=",uart.uart_get_ok)
#         uart.uart_receive_str = ''
#         uart.uart_get_ok = 0

    uart.uart_receive_str = ''
    uart.uart_get_ok = 0
  

def uart_data_handle(uart_data):
    global voice_flag,car_speed,car_turn_speed,car_turn_angle,car_turn_time
    # 唤醒指令
    if '$WAKE!' in uart_data:
        print('$WAKE!')
        car_stop()
        time.sleep(1)
#         voice_flag = 1
    # 停止指令
    elif '$TZ!' in uart_data:
        print('$TZ!')
        car_stop()
        time.sleep(1)
    # 前进指令
    elif '$QJ!' in uart_data:
        print('$QJ!')
        car_run(car_run_speed,0)   #一直前进
        time.sleep(1)

    # 后退指令
    elif '$HT!' in uart_data:
        print('$HT!')
        car_run(-car_run_speed,0)
        time.sleep(1)

    # 左转指令
    elif '$ZZ!' in uart_data:
        print('$ZZ!')
        car_stop()
        time.sleep(1)
        car_run_and_turn(car_turn_speed,car_turn_angle,0)
        time.sleep(1)

    # 右转指令
    elif '$YZ!' in uart_data:
        print('$YZ!')
        car_stop()
        time.sleep(1)
        car_run_and_turn(car_turn_speed,-car_turn_angle,0)
        time.sleep(1)

#     elif '$ZPY!' in uart_data:
#         print('$ZPY!')
#         Srt = '#021P2000T1000!'
#         print(Srt)
#         uart.uart_send_str(Srt)
#         time.sleep(1)
#     elif '$YPY!' in uart_data:
#         print('$YPY!')
#         Srt = '#021P1000T1000!'
#         print(Srt)
#         uart.uart_send_str(Srt)
#         time.sleep(1)

######################同学们需要在 loop_ps2()函数中增加自己的按键功能##########################
#3.4 处理PS2手柄输入
def loop_ps2(): 
    global arm_move_tag,car_move_tag
    global arm_servo_1_pwm,arm_servo_2_pwm,arm_servo_3_pwm,arm_servo_4_pwm
    global speed_pwm
    global fancy_mode

    if not ps2.read_gamepad():
        return
    
    ######################这里是 “START”按键的应用示范########################## 
    if ps2.ButtonPressed('START'):
        car_servos_init()
        time.sleep(1)
        arm_servos_init()
        time.sleep(1)
        print("Start button pressed. ")

    ######################请同学们自己补充各个按键功能 开始##########################

    # 左摇杆X轴控制前进/后退，Y轴控制转弯
    left_x = ps2.Analog(8)  # X轴，控制前进后退
    left_y = ps2.Analog(7)  # Y轴，控制转弯
    print(f"left_x={left_x}, left_y={left_y}")
    dead_zone = 8
    center = 128
    max_pwm = 1000
    max_angle = 400  # 最大转向角度

    # 前进/后退
    if left_x < center - dead_zone:
        speed_pwm = int((center - left_x) / (center - 0) * max_pwm)
        run_speed = speed_pwm
    elif left_x > center + dead_zone:
        speed_pwm = int((left_x - center) / (255 - center) * max_pwm)
        run_speed = -speed_pwm
    else:
        run_speed = 0

    # 转弯
    if left_y < center - dead_zone:
        turn_angle = int((center - left_y) / (center - 0) * max_angle)
    elif left_y > center + dead_zone:
        turn_angle = -int((left_y - center) / (255 - center) * max_angle)
    else:
        turn_angle = 0

    if run_speed != 0 or turn_angle != 0:
        car_run_and_turn(run_speed, turn_angle, 0)
        car_move_tag = 1
    else:
        car_stop()
        car_move_tag = 0

    # 三角形键切换花式轮子动作
    if ps2.ButtonPressed('TRIANGLE'):
        fancy_mode = not fancy_mode
        if fancy_mode:
            fancy_wheel_action(300)
            car_move_tag = 1
        else:
            car_stop()
            car_move_tag = 0

    ######################请同学们自己补充各个按键功能 结束##########################
        
    #四、主函数定义

def z_main_test():
    global nled,beep,key,ps2,uart
    
    nled = Mars_LED()                                    # 实例化一个led灯对象
    beep = Mars_BEEP()                                   # 实例化一个蜂鸣器对象
    key = Mars_KEY()                                     # 实例化按键对象
    uart = Mars_UART()                                   # 实例化串口对象

   #################################此处是手柄实例化及初始化 开始#################################### 
    ps2 = Mars_PS2()                                     # 实例化手柄对象
    # 让手柄震动以表明启动完成
    error = ps2.config_gamepad(pressures=True, rumble=True)
    if error:
        print("Error configuring controller")
        while True:
            pass  # 如果配置失败，进入无限循环
    print("Found Controller, configured successful")

    # 让手柄震动以表明启动完成
    if ps2.en_Rumble:
        print("Vibrating controller for 1 second...")
        ps2.read_gamepad(True, 255)  # 启动震动
        time.sleep(1)
        ps2.read_gamepad(False, 0)  # 停止震动
   #################################此处是手柄实例化及初始化 结束#################################### 
    #初始化车子和机械臂

    #car_arm_initial()
    
    beep.beep_on_times(3,0.1)                          # 启动完成
    
    print('main init ok')
    
    uart.uart_send_str('0,10,10\r\n')
    #################################此处是主程序进入无线循环#################################### 
    while 1:                                           # 无限循环
        loop_nled()
        loop_uart()
        loop_ps2()                                     # 手柄数据读写
        
        time.sleep(0.1)