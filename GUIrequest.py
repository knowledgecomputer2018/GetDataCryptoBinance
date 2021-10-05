try:
    import tkinter as tk # Python 3.x
    import tkinter.scrolledtext as ScrolledText
except ImportError:
    import Tkinter as tk # Pyth
from datetime import datetime,timedelta
import logging
from tkinter import *
from GetHistoricalCandle import  main
from threading import Thread


format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,datefmt="%H:%M:%S")

class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure()
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

class BinanceGUI_Request(tk.Frame):
    def __init__(self,parent, *args, **kwargs):
        self.currentDT = datetime.now()
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root=parent

        self.frameconfig=tk.Frame(master=self.root,relief=tk.SUNKEN, bg="blue")
        self.frameconfig.grid(row=0,column=0)
        #....
        self.st = ScrolledText.ScrolledText(master=self.frameconfig,width=100)
        self.st.configure(font='TkFixedFont')
        self.st.grid(column=0, row=5, )#important
        #...
        self.typecandle=IntVar()
        self.typecandle.set(1)
        #...............
        self.typefile=IntVar()
        self.typefile.set(1)
        #..........config vars
        self.frameRequest=tk.Frame(master=self.frameconfig,bg='black')
        self.frameRequest.grid(row=0,column=0,sticky="ew",padx=5, pady=5)
#................
        self.entry_request()

        #............
        self.frametypeCandle=tk.Frame(master=self.frameconfig,bg='white')
        self.frametypeCandle.grid(row=1,column=0,sticky="ew",padx=5, pady=5)
        #....................................
        self.build_gui()

        #......................................

        self.thread1 = None
        self.stop_thread=False
    def entry_request(self):
        self.entry_currency =tk.Entry(master=self.frameRequest)
        self.entry_startTime =tk.Entry(master=self.frameRequest)
        self.entry_endTime =tk.Entry(master=self.frameRequest)
        self.entry_interval =tk.Entry(master=self.frameRequest)
    def request_elem(self):
        lbl_request_des = tk.Label(master=self.frameRequest,text="request values")
        lbl_request_des.grid(row=0,column=0,sticky="ew",padx=5, pady=5)


        lbl_currency =tk.Label(master=self.frameRequest,text="Currency")
        lbl_currency.grid(row=1,column=0,sticky="ew",padx=5, pady=5)

        self.entry_currency =tk.Entry(master=self.frameRequest)
        self.entry_currency.grid(row=1,column=1,sticky="ew",padx=5, pady=5)
        self.entry_currency.insert(0,'ADAUSDT')


        lbl_startTime =tk.Label(master=self.frameRequest,text="Start-Time")
        lbl_startTime.grid(row=1,column=2,sticky="ew",padx=5, pady=5)

        self.entry_startTime =tk.Entry(master=self.frameRequest)
        self.entry_startTime.grid(row=1,column=3,sticky="ew",padx=5, pady=5)
        self.entry_startTime.insert(0,'2019/4/19')

        lbl_endTime =tk.Label(master=self.frameRequest,text="End-Time")
        lbl_endTime.grid(row=1,column=4,sticky="ew",padx=5, pady=5)

        self.entry_endTime =tk.Entry(master=self.frameRequest)
        self.entry_endTime.grid(row=1,column=5,sticky="ew",padx=5, pady=5)
        self.entry_endTime.insert(0,'2020/4/19')

        lbl_inteval =tk.Label(master=self.frameRequest,text="Interval")
        lbl_inteval.grid(row=1,column=6,sticky="ew",padx=5, pady=5)
        self.entry_interval =tk.Entry(master=self.frameRequest)
        self.entry_interval.grid(row=1,column=7,sticky="ew",padx=5, pady=5)
        self.entry_interval.insert(0,'5')

    def TypeCandle_elem(self):
        #frametypesell=tk.Frame(master=self.frameRequest,bg='yellow')


        lbl_select_typesell = tk.Label(master=self.frametypeCandle,text="Select_typeCandle")
        lbl_select_typesell.grid(row=2,column=0,sticky="ew",padx=5, pady=5)

        rdo1=tk.Radiobutton(master=self.frametypeCandle,text="minute",variable=self.typecandle,value=1)
        rdo1.grid(row=3,column=0,sticky="ew", padx=5, pady=5)

        rdo2=tk.Radiobutton(master=self.frametypeCandle,text="hour",variable=self.typecandle,value=2)
        rdo2.grid(row=3,column=1,sticky="ew", padx=5, pady=5)

        rdo3=tk.Radiobutton(master=self.frametypeCandle,text="day",variable=self.typecandle,value=3)
        rdo3.grid(row=3,column=2,sticky="ew", padx=5, pady=5)

        rdo4=tk.Radiobutton(master=self.frametypeCandle,text="week",variable=self.typecandle,value=4)
        rdo4.grid(row=3,column=4,sticky="ew", padx=5, pady=5)

        rdo5=tk.Radiobutton(master=self.frametypeCandle,text="month",variable=self.typecandle,value=5)
        rdo5.grid(row=3,column=5,sticky="ew", padx=5, pady=5)
    def TypeFile_elem(self):
        #frametypesell=tk.Frame(master=self.frameRequest,bg='yellow')


        lbl_select_typesell = tk.Label(master=self.frametypeCandle,text="Select_typeFile")
        lbl_select_typesell.grid(row=4,column=0,sticky="ew",padx=5, pady=5)

        rdo1=tk.Radiobutton(master=self.frametypeCandle,text="csv",variable=self.typefile,value=1)
        rdo1.grid(row=5,column=0,sticky="ew", padx=5, pady=5)

        rdo2=tk.Radiobutton(master=self.frametypeCandle,text="xml",variable=self.typefile,value=2)
        rdo2.grid(row=5,column=1,sticky="ew", padx=5, pady=5)

        rdo3=tk.Radiobutton(master=self.frametypeCandle,text="json",variable=self.typefile,value=3)
        rdo3.grid(row=5,column=2,sticky="ew", padx=5, pady=5)

    def btn_gui(self):
        self.root.title('BinanceAnalyseData')
        #self.root.option_add('*tearOff', 'FALSE')


        #tk.Frame,tk.Frame.__init__(self, parent, *args, **kwargs) and five line upone(relationship)
        '''
        self.grid(column=0, row=0, sticky='ew')

        self.grid_columnconfigure(0, weight=1, uniform='a')
        self.grid_columnconfigure(1, weight=1, uniform='a')
        self.grid_columnconfigure(2, weight=1, uniform='a')
        self.grid_columnconfigure(3, weight=1, uniform='a')
        '''

        # Add text widget to display logging info





         # Create textLogger
        text_handler = TextHandler(self.st)

                # Logging configuration
        logging.basicConfig(filename='test.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s')

       # Add the handler to logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(text_handler)

        frame_btn=tk.Frame(master=self.frameconfig,relief=tk.SUNKEN, bg="red")

        btn1=tk.Button(master=frame_btn,text='Quit',command=self.root.destroy)
        btn1.grid(row=0,column=0,sticky="nsew", padx=5, pady=5)

        btn2=tk.Button(master=frame_btn,text='RUN', command=self.thread_historical)

        btn2.grid(row=0,column=2,sticky="ew", padx=5, pady=5)

        frame_btn.grid(row=2,column=0,padx=5, pady=5)
    def build_gui(self):
        #................................................................request_elem
        self.request_elem()
        #............................................................................typecandle
        self.TypeCandle_elem()
        #............................................................................
        self.TypeFile_elem()
        #............................................................................
        self.btn_gui()
        #............................................................................
    def thread_historical(self):
        self.thread1=Thread(target=self.run)
        self.thread1.start()#?
    def get_rdo(self):

        global typecandlegui
        if(self.typecandle.get()==1):
            logging.info("Candle type: minute")
            typecandlegui='m'
        elif(self.typecandle.get()==2):
            logging.info("Candle type: hour")
            typecandlegui='h'
        elif(self.typecandle.get()==3):
            logging.info("Candle type: day")
            typecandlegui='d'
        elif(self.typecandle.get()==4):
            logging.info("Candle type: week")
            typecandlegui='w'
        elif(self.typecandle.get()==5):
            logging.info("Candle type: month")
            typecandlegui='M'
        return typecandlegui
    def get_rdo_file(self):
        global typefilegui
        if(self.typefile.get()==1):
            logging.info("file type: csv")
            typefilegui='csv'
        elif(self.typefile.get()==2):
            logging.info("file type: xml")
            typefilegui='xml'
        elif(self.typefile.get()==3):
            logging.info("file type: json")
            typefilegui='json'

        return typefilegui
    def get_selected_chk_FILE(self):
        return self.get_rdo_file()
    def get_selected_chk(self):
        return self.get_rdo()
    def get_values_gui(self):
        dic_values={
            'request_values':{

             'typefile':self.get_selected_chk_FILE(),
             'time':   self.get_selected_chk(),
             'interval':self.entry_interval.get(),
             'startDate':self.entry_startTime.get(),
             'endDate':self.entry_endTime.get(),
             'symbol':self.entry_currency.get()
            }
        }
        return dic_values
    def run(self):
        dic_values=self.get_values_gui()

        #logging.info(json_values['typesell'])
        main(dic_values)


def main_gui():
    win=tk.Tk()


    logging.info("In the name of god .")
    logging.info("i am in file BinanceGUI_Request")
    BinanceGUI_Request(win)
    win.mainloop()
logging.info("Start GUIRequest")
t0 = Thread(target=main_gui, args=[])
t0.start()
t0.join()
logging.info("End GUIRequest")
