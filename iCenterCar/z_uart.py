'''
修改信息
作者：郑养波
日期：2025年6月1日
esp32有3个串口，UART0给程序调试下载使用，一般做成TPYEC；
本程序是UART2,也就是2号串口
硬件上还预留了UART1，也就是串口1给其他扩展使用
'<': '>',   # Type1: <...> 格式
'{': '}',   # Type2: {...} 格式
'#': '!',   # Type3: #...! 格式
'$': '!'    # Type4: $...! 格式
'''
from machine import UART
import time

#from iCenterRobot.z5_hcsr04 import Robot_HCSR04
#import iCenterRobot.z6_sensor as Robot_AI
#import iCenterRobot.z9_car as Robot_CAR

SPEED_PWM_VOI = 150

class Robot_UART(object):

    def __init__(self, baud=115200):
        self.uart2 = ''                                             # 串口2
        self.baud = baud                                            # 波特率
        self.mode = 0
        self.uart_get_ok = 0
        self.uart_receive_str = ''
         # 定义帧类型及其对应的结束符：<...> {...} #...! $...!
        self.uart_send_flag = 0

        self.uart2 = UART(2, self.baud)                             # 使用给定波特率初始化
        self.uart2.init(self.baud, bits=8, parity=None, stop=1)     # 使用给定参数初始化
        self.uart2.write('uart2 init ok!\r\n')

    #发送字符串 只需传入要发送的字符串即可
    def uart_send_str(self, temp):
        self.uart_send_flag = 1
        self.uart2.write(temp)                                      # 串口发送数据
        ##此处代表发送完，把总线写成接收状态
        self.uart_send_flag = 0

    # 串口接收数据，主要处理数据接受格式，主要格式为<...> {...} $...!  #...! 4种格式，...内容长度不限
    def recv_str(self):
        if self.uart2.any() > 0:
            # 每次最多读取128字节，避免内存溢出
            uart2_recv_data = self.uart2.read()
            print("before1", self.uart_receive_str)
        
            try:
                self.uart_receive_str += uart2_recv_data.decode('utf-8')
            except UnicodeError:
                return
#             self.uart_receive_str = self.uart_receive_str + uart2_recv_data.decode("utf-8","ignore")
            print("before2", self.uart_receive_str)
            
        if self.uart_send_flag:
            self.uart_receive_str = ''
            self.uart_send_flag = 0
#             print("if self.uart_send_flag")
            return
    
        if len(self.uart_receive_str) < 2:
#             print("if len(self.uart_receive_str) < 2")
            return
        
        self.mode = 0
        
        if self.mode == 0:
            if self.uart_receive_str.find('<') >= 0:
                self.mode = 1
                #print('mode1 start')
            elif self.uart_receive_str.find('{') >= 0:
                self.mode = 2
                #print('mode2 start')
            elif self.uart_receive_str.find('#') >= 0:
                self.mode = 3
                #print('mode3 start')
            elif self.uart_receive_str.find('$') >= 0:
                self.mode = 4
                #print('mode4 start')
        
        if self.mode == 1:
            if self.uart_receive_str.find('>') >= 0:
                self.uart_get_ok = 1
                self.mode = 0
                #print('mode1 end')
        elif self.mode == 2:
            if self.uart_receive_str.find('}') >= 0:
                self.uart_get_ok = 2
                self.mode = 0
                #print('mode2 end')
        elif self.mode == 3:
            if self.uart_receive_str.find('!') >= 0:
                self.uart_get_ok = 3
                self.mode = 0
                #print('mode3 end')
        elif self.mode == 4:
            if self.uart_receive_str.find('!') >= 0:
                self.uart_get_ok = 4
                self.mode = 0
                #print('mode4 end')
                
#         print("end ", "self.uart_get_ok=", self.uart_get_ok, "self.mode=", self.mode)

def UART_Initial():
    global uart
    uart = Robot_UART()
    
def UART_send_str(temp):
    uart.uart_send_str(temp)
    
def UART_recv_str():
    
    uart.recv_str()
    
    if uart.uart_get_ok == 1:
        print("Camera data") 
        uart_data_handle_1(uart.uart_receive_str)         # 处理接收的数据-摄像头数据
    
    if uart.uart_get_ok == 2 or uart.uart_get_ok == 3:
        print("uart data is type 1 or type 2")

    #类似$111！——语音数据
    if uart.uart_get_ok == 4:
        print("Voice data") 
        uart_data_handle_4(uart.uart_receive_str)         # 处理接收的数据-语音控制

    uart.uart_receive_str = ''
    uart.uart_get_ok = 0

def uart_data_handle_1(uart_data):
#     global uart
    xc_zhilin = uart_data
    print(xc_zhilin)
#                 print(int(time.time()*1000))
    if xc_zhilin[0:3] == '<qd' and  xc_zhilin[9:10] == ">":                  # 坐标移动
                    #前进
        buju_x = int(xc_zhilin[3:6])
        buju_y = int(xc_zhilin[6:9])
        print(buju_x)
        print(buju_y)
        if buju_x != 0:
            if   buju_x > 0:
               #Robot_CAR.qianjin(100)
               #time.sleep((buju_x)) # 6cm
               time.sleep(0.1)
            else:
               #Robot_CAR.houtui(100)
               time.sleep(abs(buju_x))
               time.sleep(0.1)
            #tingzhi()
        if buju_y != 0:
            if   buju_y < 0:
                #Robot_CAR.zuopingyi(120)
               #time.sleep(abs(buju_y))
                time.sleep(0.1)
            else:
                #Robot_CAR.youpingyi(120)
                #time.sleep(abs(buju_y))
                time.sleep(0.1)
            #Robot_CAR.tingzhi()
        uart.uart_send_str("daoda")
        buju_x = 0
        buju_y = 0 
        print('1111')
                
    elif xc_zhilin[0:3] == '<rw' and  xc_zhilin[9:10] == ">":
        buju_x = int(xc_zhilin[3:9])
        print(buju_x)
        #Robot_AI.car_xunji()
        buju_x = 0
        buju_y = 0 
        uart.uart_send_str("daoda")
        print('2222')
    elif xc_zhilin[0:3] == '<ap' and  xc_zhilin[9:10] == ">":
        buju_x = int(xc_zhilin[3:6])/6
        buju_y = int(xc_zhilin[6:9])/7
        print(buju_x)
        print(buju_y)
        #if buju_x != 0:
        #    if   buju_x > 0:
        #        youpginyi(100)
         #       time.sleep(buju_x)
         #   else:
         #       zuopingyi(100)
         #       time.sleep(abs(buju_x))                   
         #   tingzhi()
        if buju_y != 0:
            if   buju_y < 0:
                #Robot_CAR.houtui(100)
                time.sleep(buju_y)
            else:
                #Robot_CAR.qianjin(100)
                time.sleep(buju_y)
        #Robot_CAR.tingzhi()
        uart.uart_send_str("daoda")
        buju_x = 0
        buju_y = 0                     
        print('3333')  
    elif xc_zhilin[0:3] == '<bj' and  xc_zhilin[9:10] == ">":   #追随运动
        buju_x = int(xc_zhilin[3:6])
        buju_y = int(xc_zhilin[6:9])
        print(buju_x)
        print(buju_y)
        if abs(buju_x) > 4:
            if   buju_x > 1:
                #Robot_CAR.zuopingyi(100)
                time.sleep(0.1)
            else:
                #Robot_CAR.youpingyi(100)
                time.sleep(0.1)                      
            #tingzhi()
        if abs(buju_y) > 4:
            if   buju_y > 0:
                #Robot_CAR.qianjin(100)
                time.sleep(0.1)
            else:
                #Robot_CAR.houtui(100)
                time.sleep(0.1)
            #Robot_CAR.tingzhi()
        if abs(buju_x) < 4 and abs(buju_y) < 4:
            uart.uart_send_str("daoda")
        else :
            uart.uart_send_str("yunxing")
        print('4444')

def uart_data_handle_4(uart_data):
    global uart

    '''
    MOVE_TAG 			0—测试；1—手柄控制；2—循迹控制；3—自由避障；4—定距跟随
    VOI_CON_TAG 		0-语音控制关闭；1-语音控制开启
    PS2_CON_TAG   		0-手柄控制关闭；1-手柄控制开启
    CAM_SIG_TAG			0-无摄像头信号；1-有摄像头信号
    '''   
    # 唤醒指令“你好小清”
    if '$WAKE!' in uart_data:
        print("huan xing")
        #Robot_CAR.tingzhi()
        time.sleep(1)
        
    #循迹控制“启动循迹控制”    
    elif '$XJ!'in uart_data:
        print("xunji")
        #Robot_AI.car_xunji()
   
    #自由避障“启动自由避障”    
    elif '$BZ!'in uart_data:
        print("bizhang")
        #Robot_AI.ziyou_bizhang()
    
    #定距跟随“启动定距跟随”    
    elif '$DJ!'in uart_data:
        print("dingju")
        #Robot_AI.dingju_gensui()
       
    # 停止指令
    elif '$TZ!' in uart_data:
        Robot_CAR.tingzhi()
        time.sleep(1)
    # 前进指令
    elif '$QJ!' in uart_data:
        print("qianjin")
        #Robot_CAR.qianjin(SPEED_PWM_VOI)
        time.sleep(1)
            
    # 后退指令
    elif '$HT!' in uart_data:
        print("houtui")
        #Robot_CAR.houtui(SPEED_PWM_VOI)
        time.sleep(1)
    # 左转指令
    elif '$ZZ!' in uart_data:
        print("zuozhuan")
        #Robot_CAR.zuozhuan(SPEED_PWM_VOI)
        time.sleep(1)
    # 右转指令
    elif '$YZ!' in uart_data:
        print("youzhuan")
        #Robot_CAR.youzhuan(SPEED_PWM_VOI)
        time.sleep(1)
    # 左平移指令
    elif '$ZPY!' in uart_data:
        print("zuopingyi")
        #Robot_CAR.zuopingyi(SPEED_PWM_VOI)
        time.sleep(1)
     # 右平移指令
    elif '$YPY!' in uart_data:
        print("youpingyi")
        #Robot_CAR.youpingyi(SPEED_PWM_VOI)
        time.sleep(1)

#程序入口
if __name__ == '__main__':
    
    UART_Initial()                                               # 实例化串口
    #Robot_CAR.PWM_Initial()   
    
#     try:                                                     # 异常处理
#         while 1:                                             # 无限循环
#             uart.recv_str()                                  # 串口接收并根据格式处理数据
#             if uart.uart_get_ok:
#                 print(int(time.time()*1000))
#                 if uart.uart_receive_str == '<$LEDON!>':
#                     uart.uart_send_str("1111")
#                     print('1111')
#                 elif uart.uart_receive_str == '{LEDON!}':
#                     uart.uart_send_str("2222")
#                     print('2222')
#                 elif uart.uart_receive_str == '$LEDON!':
#                     uart.uart_send_str("3333")
#                     print('3333')
#                 elif uart.uart_receive_str == '#LEDON!':
#                     uart.uart_send_str("4444")
#                     print('4444')
# 
#                 uart.uart_receive_str = ''
#                 uart.uart_get_ok = 0
# 
#     except:
#         pass
