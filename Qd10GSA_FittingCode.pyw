# -*- coding: UTF-8 -*-
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import platform
import numpy as np
import math
import random
import sys
import time
import os
try:
    import matplotlib.pyplot as plt
    import matplotlib as mpl
except:
    pass
np.seterr(invalid='ignore')

class Fitting(Tk):
    __author__ = "Kleber C. Mundim, Hugo G. Machado"
    __version__ = "1.0.1"
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self.geometry("800x650+100+100")
        self.title('Qd10GSA Fitting - Vesion:{}'.format(self.__version__))
        #self.resizable(False, False)

        ### Menu
        menu = Menu(self)
        self.config(menu=menu)
        subMenu = Menu(menu)
        menu.add_cascade(label='Help', menu=subMenu)
        subMenu.add_command(label='Help', command = self.Help)
        subMenu.add_command(label='About', command = self.About)
        subMenu.add_separator()
        subMenu.add_command(label='Exit', command = self.Exit)

        ### Title
        ttk.Label(self, text="Qd10GSA Fitting", font=('arial', 30, 'bold')).pack(pady=10)

        ### dicts (entrada de dados, variáveis, labels checkbuttons)
        self.ed = {} ; self.Var = {} ; self.lb = {} ; self.cb = {}

        ### dicts (parâmetros dos ajustes de cada teoria)
        self.ChiSq = {} ; self.X_Min = {} ; self.YFit = {} ; self.XFit = []

        ### LEFT
        frame_left = ttk.Frame(self)
        frame_left.pack(side=LEFT, padx=30,fill=BOTH)

        lb_gsa = ttk.Label(text='GSA Parameters',style='Wild.TLabel')
        frame_gsaPar = ttk.LabelFrame(frame_left, labelwidget=lb_gsa, borderwidth=5,)
        frame_gsaPar.pack(side=TOP, pady=7, fill=BOTH)
        self.CriarFrameGSAPar(frame_gsaPar)

        lb_fit = ttk.Label(text='Model Parameters',style='Wild.TLabel')
        frame_par = ttk.LabelFrame(frame_left,labelwidget=lb_fit)
        frame_par.pack(side=TOP, pady=7, fill=BOTH)

        self.configure_tabs(frame_par)

        self.Arr_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.Arr_tab, text="Arrhenius")

        self.dArr_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.dArr_tab, text="d-Arrhenius")

        if os.path.isfile('GSA.in'):
            try:
                with open('GSA.in','r') as f:
                    txt = f.readlines()
                ini = txt[7].split()
                ini = [float(x) for x in ini]
            except:
                ini = None
        else:
            ini = None

        for tab,theory in [(self.Arr_tab,'Arr'),(self.dArr_tab,'dArr')]:
            self.CriarFrameParameter(tab,theory,ini)
        self.ed[10]['style'] = 'Wild.TEntry'
        self.ed[10]['state'] = DISABLED
        lb_plot = ttk.Label(text='Plot',style='Wild.TLabel')
        frame_plot= ttk.LabelFrame(frame_left,labelwidget=lb_plot,borderwidth=5)
        frame_plot.pack(fill=BOTH,pady=0)
        self.CriarPlotFrame(frame_plot)

        ### MIDDLE
        frame_middle = ttk.Frame(self,borderwidth=5)
        frame_middle.pack(side=LEFT, padx=15,fill=BOTH)

        lb_box = ttk.Label(text='Input Data',style='Wild.TLabel')
        frame_middle_inp = ttk.LabelFrame(frame_middle, labelwidget=lb_box,borderwidth=5)
        frame_middle_inp.pack()


        frame_middle_box = ttk.Frame(frame_middle_inp)
        frame_middle_box.pack(side=TOP, pady=7, )
        self.CriarBoxScroll(frame_middle_box)

        frame_input_format = ttk.Frame(frame_middle_inp)
        frame_input_format.pack(side=TOP,pady=0)
        self.CreateInputFormat(frame_input_format)

        frame_bt = ttk.Frame(frame_middle)
        frame_bt.pack(side=BOTTOM,pady=15)
        self.CriarButton(frame_bt)

    def configure_tabs(self,parent):
        for rows in range(0,50):
            parent.rowconfigure(rows, weight=1)
            parent.columnconfigure(rows, weight=1)
            rows += 1
        self.tabs = ttk.Notebook(parent,style='Wild.TFrame')
        self.tabs.pack(anchor=W,padx=15,pady=5)

    def CriarFrameGSAPar(self,parent):
        frames = {}

        for ind, txt,value in [('qA', 'Acceptance index', 1.0),
                ('qT', 'Temperature index', 1.1),
                ('qV', 'Visiting index', 1.1),
                ('To', 'Initial Temperature',1),
                ('N', 'Number of GSA-loops',10000000)]:
            frames[ind] = ttk.Frame(parent)
            frames[ind].pack(padx= 15, pady=8, anchor=W)
            self.ed[ind] = ttk.Entry(frames[ind])
            self.ed[ind].pack(side=LEFT)
            self.ed[ind].insert(0, value)
            ttk.Label(frames[ind], text="({}) - {}".format(ind,txt)).pack(side=RIGHT)

    def CriarFrameParameter(self,parent,theory,initial=None):
        self.filename = ''
        self.ChiSq[theory] = ttk.Label(parent, text='Chi-square: ')
        self.ChiSq[theory].pack(anchor=W, pady=5)

        if initial == None:
            ini = [10,100,0.001]
        else:
            ini = initial

        self.f_init_par = {}
        for ind, a, value in {'dArr':[(0,'ln(A)',ini[0]),(1,'Eo',ini[1]),(2,'d      ',ini[2])],'Arr':[(3,'ln(A)',ini[0]),(4,'Eo',ini[1]), (10,'d      ','')]}[theory]:
            self.f_init_par[ind] = ttk.Frame(parent)
            self.f_init_par[ind].pack(pady=7, anchor=W)
            ttk.Label(self.f_init_par[ind], text='{:6s}'.format(a)).pack(side=LEFT,padx=5)
            self.ed[ind] = ttk.Entry(self.f_init_par[ind])
            self.ed[ind].pack(side=LEFT, padx=35)
            self.ed[ind].insert(0, value)

    def CriarPlotFrame(self,parent):
        frame1 = ttk.Frame(parent) ; frame1.pack(side=LEFT)
        frame2 = ttk.Frame(parent) ; frame2.pack(side=LEFT)

        for frame, txt, cmd, padx in [(frame1,'ln(k) x 1000/RT',lambda x=1: self.PlotRate(x),26),
                         (frame1,'k x log10(T)', lambda x=2: self.PlotRate(x),26),
                         (frame2,'Ea x T',self.PlotEa,0),
                         (frame2,'Qd10 x T2',self.PlotQd10,0)]:

            Button(frame, text=txt, command=cmd, width=15,relief=RIDGE,font=('Arial',9)).pack(pady = 12, padx=padx, anchor=W)

    def CreateInputFormat(self,parent):
        frame1 = ttk.Frame(parent) ; frame1.pack(side=LEFT)
        frame2 = ttk.Frame(parent) ; frame2.pack(side=LEFT)

        padx = 50
        pady=0
        self.TVar = StringVar()
        T = ttk.Radiobutton(frame1, text='T    ', variable=self.TVar, value='T') ; T.pack(side=TOP,anchor=W,padx=padx,pady=pady)
        T.invoke()
        Tinv = ttk.Radiobutton(frame1, text='1/T  ', variable=self.TVar, value='Tinv') ; Tinv.pack(side=TOP,anchor=W,padx=padx,pady=pady)
        RTinv = ttk.Radiobutton(frame1, text='1/RT ', variable=self.TVar, value='1000RTinv') ; RTinv.pack(side=TOP,anchor=W,padx=padx,pady=pady)

        self.kVar = StringVar()
        lnk = ttk.Radiobutton(frame2, text='ln(k)', variable=self.kVar, value='lnk') ; lnk.pack(side=TOP,  anchor=W,padx=padx,pady=pady)
        lnk.invoke()
        k = ttk.Radiobutton(frame2, text='k   ', variable=self.kVar, value='k') ; k.pack(side=TOP,anchor=W,padx=padx,pady=pady)
        log10k = ttk.Radiobutton(frame2, text='log10k', variable=self.kVar, value='log10(k)') ; log10k.pack(side=TOP,anchor=W,padx=padx,pady=pady)

    def CriarBoxScroll(self,parent):
        parent1 = ttk.Frame(parent);parent1.pack()
        parent2 = ttk.Frame(parent);parent2.pack()

        frame01 = ttk.Frame(parent1) ; frame01.pack(side=LEFT)
        frame02 = ttk.Frame(parent1) ; frame02.pack(side=LEFT)

        ttk.Label(frame01, text='Temperature', font=('arial', 10)).pack(padx=35)
        ttk.Label(frame02, text='Rate Constant', font=('arial', 10)).pack(padx=35)

        frame1 = ttk.Frame(parent2) ; frame1.pack(side=LEFT)
        frame2 = ttk.Frame(parent2) ; frame2.pack(side=LEFT,)

        height = 22
        width = 19

        ### Temperature
       # ttk.Label(frame1, text='Temperature', font=('arial', 10)).pack(padx=15, expand=True)
        self.txt_l = Text(frame1, height=height, width=width,relief=FLAT)
        self.txt_l.pack(fill=BOTH, expand=True, padx=3)

        ### Rate Constante
        #ttk.Label(frame2, text='Rate Constant', font=('arial', 10)).pack(padx=15, expand=True)
        self.txt_r = Text(frame2, height=height, width=width,relief=FLAT)
        self.txt_r.pack(fill=BOTH, expand=True, padx=3)

        self.scrollbar = ttk.Scrollbar(parent2)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        # Changing the settings to make the scrolling work
        self.scrollbar['command'] = self.on_scrollbar
        self.txt_l['yscrollcommand'] = self.on_textscroll
        self.txt_r['yscrollcommand'] = self.on_textscroll

    def on_scrollbar(self, *args):
        self.txt_l.yview(*args)
        self.txt_r.yview(*args)

    def on_textscroll(self, *args):
        self.scrollbar.set(*args)
        self.on_scrollbar('moveto', args[0])

    def CriarButton(self,parent):
        self.bt = {}
        for txt, cmd in [('Open file',self.Open),
                         ('Clear',self.Clear),
                         ('Fitting', self.Fit),
                         ('Save',self.Save)]:
            self.bt[txt] = Button(parent, text=txt, command=cmd, width=8,relief=RIDGE,font=('Arial',10))#, font=('Arial', 10,'bold'), width=8,height=1)
            self.bt[txt].pack(side=LEFT,expand=True,pady = 14, padx=7, anchor=E)

    def RateUnitChange(self):
        """ Default = ln(k)
        k e log10(k0 se selecionados serão convertidos para k """
        if self.kVar.get() == 'k':
            self.Yexp = np.log(self.Yexp)
        if self.kVar.get() == 'log10k':
            self.Yexp = 10 ** self.Yexp
            self.Yexp = np.log(self.Yexp)

    def TUnitChange(self):
        """Default = T (K)
        1/T e 1/RT se selecionados serão convertidos para T"""
        if self.TVar.get() == 'Tinv':
            self.Xexp = 1/self.Xexp

        if self.TVar.get() == '1000RTinv':
            self.Xexp = 1000/(self.Xexp*8.314472)

    def PlotRate(self,format):

        if len(self.X_Min) == 0:
            messagebox.showerror(title='Error', message='Fitting First')
            return

        fig, (ax) = plt.subplots(1, 1)

        if format == 1:
            ax.scatter(self.XFit, self.Yexp, label='Experimental',c= 'darkgoldenrod')
            for theory in sorted(self.X_Min):
                label = {'dArr': 'd-Arrhenius', 'Arr':'Arrhenius'}[theory]
                ls = {'dArr': '-', 'Arr': '--'}[theory]
                ax.plot(self.XFit, self.YFit[theory], label=label, linestyle=ls, c = {'Arr':'b','dArr':'r'}[theory]  )
            ax.set(xlabel="1000/RT", ylabel='ln(k)')

        if format == 2:
            ax.scatter(np.log(self.Xexp), np.exp(self.Yexp), label='Experimental',c= 'darkgoldenrod')
            for theory in sorted(self.X_Min):
                label = {'dArr': 'd-Arrhenius', 'Arr':'Arrhenius'}[theory]
                ls = {'dArr': '-', 'Arr': '--'}[theory]
                ax.plot(np.log(self.Xexp), np.exp(self.YFit[theory]), label=label,linestyle=ls, c = {'Arr':'b','dArr':'r'}[theory]  )
            ax.set(xlabel="Log10(T)", ylabel='k')

        ax.grid(True)
        plt.legend(loc='best', shadow=False, fontsize='x-large')
        plt.show()

    def PlotEa(self):
        if len(self.X_Min) == 0:
            messagebox.showerror(title='Error', message='Fitting First')
            return

        fig, (ax) = plt.subplots(1, 1)

        if 'Arr' in self.X_Min:
            lnA, Eo, d = self.X_Min['Arr']
            ax.plot(self.Xexp, np.ones(len(self.Xexp)) * (Eo/1000), label='Arrhenius',linestyle='--', color='b')

        if 'dArr' in self.X_Min:
            lnA, Eo, d = self.X_Min['dArr']
            Ea = Eo*( 1 / (1-( (d*Eo) / (8.314472 * self.Xexp) )))
            ax.plot(self.Xexp, Ea/1000, label='d-Arrhenius', color='r')

        ax.set(xlabel="Temperature (K)", ylabel='Activation Energy (kJ/mol)')
        ax.grid(True)
        plt.legend(loc='best', shadow=False, fontsize='x-large')
        plt.show()

    def PlotQd10(self):
        if len(self.X_Min) == 0:
            messagebox.showerror(title='Error', message='Fitting First')
            return
        if 'Arr' in self.X_Min:
            lnA, Eo, d = self.X_Min['Arr']
        if 'dArr' in self.X_Min:
            dlnA, dEo, d = self.X_Min['dArr']

        dQ10 = []
        Q10 = []
        for n in range(len(self.Xexp)-1):
            T1 = self.Xexp[n]
            T2 = self.Xexp[n + 1]
            if 'Arr' in self.X_Min:
                f1 =  np.exp( -Eo / (8.314472 * T1) )
                f2 =  np.exp( -Eo / (8.314472 * T2) )
                Q10.append( (f2 / f1) ** (10.0 / (T2-T1)) )
            if 'dArr' in self.X_Min:
                df1 = (1.0- ((d * dEo) / (8.314472 * T1))) ** (1.0 / d)
                df2 = (1.0- ((d * dEo) / (8.314472 * T2))) ** (1.0 / d)
                dQ10.append( (df2 / df1) ** (10.0 / (T2-T1)) )

        fig, (ax) = plt.subplots(1, 1)
        if 'Arr' in self.X_Min:
            ax.plot(self.Xexp[1:], Q10, label='Q10 (Arrhenius)',linestyle='--', color='b')
        if 'dArr' in self.X_Min:
            ax.plot(self.Xexp[1:], dQ10, label='d-Q10 (d-Arrhenius)', linestyle='-', color='r')

        ax.set(xlabel="T2", ylabel='Q10')
        ax.grid(True)
        plt.legend(loc='best', shadow=False, fontsize='x-large')
        plt.show()

    def Open(self):
        self.filename = filedialog.askopenfilename(title="Select file",filetypes=[(".txt files", "*.txt;*.dat;*.csv"), ("all files", "*.*")])
        if not os.path.isfile(self.filename):
            return
        self.txt_l.delete(0.0, END)
        self.txt_r.delete(0.0, END)
        for delimiter in ['\t', ',', ';']:
            try:
                dados = np.loadtxt(self.filename, delimiter=delimiter)
            except:
                try:
                    dados = np.loadtxt(self.filename, delimiter=delimiter,skiprows=1)
                except:
                    pass
        try:
            X, Y = dados[:, 0], dados[:, 1]
        except:
            messagebox.showerror(title='Error', message='Select file in csv format')
            return

        for i in range(len(X)):
            self.txt_l.insert(float(i + 1), str(X[i]) + '\n')
            self.txt_r.insert(float(i + 1), str(Y[i]) + '\n')

        self.Clear()

    def Clear(self):
        for ind,txt in zip(range(5),['10','100','0.001','10','100']):
            self.ed[ind].delete(0, END)
            self.ed[ind].insert(0, txt)
        self.ChiSq['Arr']['text'] = ' Chi-square: '
        self.ChiSq['dArr']['text'] = ' Chi-square: '
        self.X_Min = {} ; self.YFit = {} ; self.XFit = []

    def Save(self):
        if len(self.X_Min) == 0:
            messagebox.showerror(title='Error', message='Fitting First')
            return

        filename = filedialog.asksaveasfilename(title="Save File", defaultextension='txt', filetypes=(("txt files", "*.txt"), ("dat files", "*.dat"), ("all files", "*.*")))
        out = open(filename, 'w', encoding="utf-8")
        for theory in self.X_Min:
            out.writelines("\t{}\n".format({'Arr':'Arrhenius','dArr':'d-Arrhenius'}[theory]))
            for ind,txt in {'dArr':[(0,'ln(A)'),(1,'Eo'),(2,'d')], 'Arr':[(0,'ln(A)'),(1,'Eo')]}[theory]:
                out.writelines('{} = {}\n'.format(txt, self.X_Min[theory][ind]))
            out.writelines('Chi-Square = {:.15f}\n\n'.format(float(self.ChiSq[theory]['text'].split()[-1])))

        T = self.Xexp
        Tinv = self.XFit
        kexp = np.exp(self.Yexp)
        kArr = np.exp(self.YFit['Arr'])
        kdArr = np.exp(self.YFit['dArr'])
        lnkexp = self.Yexp
        lnkArr = self.YFit['Arr']
        lnkdArr = self.YFit['dArr']

        out.writelines('\n{:^20s} {:^20s} {:^20s} {:^20s} {:^20s}\n'.format('T', '1000/RT','lnk_Exp', 'ln(k)_Arrhenius','ln(k)_d-Arrhenius'))
        for n in range(len(self.Xexp)):
            a = '{:>.15f}'.format(T[n])
            b = '{:>.15f}'.format(Tinv[n])
            c = '{:>.15f}'.format(lnkexp[n])
            d = '{:>.15f}'.format(lnkArr[n])
            e = '{:>.15f}'.format(lnkdArr[n])
            out.writelines('{:>20s} {:>20s} {:>20s} {:>20s} {:>20s}  \n'.format(a, b, c, d, e))
        out.writelines('\n')
        out.writelines('\n{:^20s} {:^20s} {:^20s} {:^20s} {:^20s}\n'.format('T', '1000/RT', 'k_Exp','k_Arrhenius', 'k_d-Arrhenius'))
        for n in range(len(self.Xexp)):
            a = '{:>.15f}'.format(T[n])
            b = '{:>.15f}'.format(Tinv[n])
            c = '{:>.15f}'.format(kexp[n])
            d = '{:>.15f}'.format(kArr[n])
            e = '{:>.15f}'.format(kdArr[n])
            out.writelines('{:>20s} {:>20s} {:>20s} {:>20s} {:>20s}  \n'.format(a,b,c,d,e))
        out.writelines('\n')
        out.close()

    def Fit(self):
        ###########################################
        ### X
        X = self.txt_l.get(0.0, END)
        X = X.split('\n')
        X_corr = [float(x) for x in X if len(x) > 0 and not x.isspace()]

        ### Y
        Y = self.txt_r.get(0.0, END)
        Y = Y.split('\n')
        Y_corr = [float(y) for y in Y if len(y) > 0 and not y.isspace()]

        if len(X_corr) != len(Y_corr):
            messagebox.showerror(title='Error', message='Difference in the number of points between X and Y ')
            return
        if len(X_corr) == 0 or len(Y_corr) == 0:
            messagebox.showerror(title='Error', message='Enter the values of X and Y ')
            return
        self.Xexp = np.array(X_corr)
        self.Yexp = np.array(Y_corr)

        self.RateUnitChange()
        self.TUnitChange()

        ###########################################
        ### Theory

        txt = self.tabs.select()
        if txt[-1] == '2': theory = 'dArr'
        else: theory = 'Arr'

        ###########################################
        ### Initial Parameters
        try:
            X_0 = []
            for n in {'dArr':range(3),'Arr':[3,4,2]}[theory]:
                X_0.append(float(self.ed[n].get()))
        except:
            messagebox.showerror(title='Error', message='Invalid Initial parameters')
            return
        ###########################################
        ### GSA parameters
        try:
            qA = float(self.ed['qA'].get())
            qT = float(self.ed['qT'].get())
            qV = float(self.ed['qV'].get())
            NStopMax = int(self.ed['N'].get())
            To = float(self.ed['To'].get())

        except:
            messagebox.showerror(title='Error', message='Invalid GSA parameters')
            return

        if theory is 'Arr':
            To = To/10

        ###########################################
        ### write data_file
        data_file = open('data.dat','w')
        for n in range(len(self.Xexp)):
            data_file.writelines('{}\t{}\n'.format(self.Xexp[n],self.Yexp[n]))
        data_file.close()

        ### Write GSA.in
        txt = [
            'Initial GSA parameters\n',
            ' {}\tqA\tAcceptance index\n'.format(qA),
            ' {}\tqT\tTemperature index\n'.format(qT),
            ' {}\tqV\tVisiting index\n'.format(qV),
            ' {}\tNStopMax\tMax number of GSA-loops\n'.format(NStopMax),
            ' {}\tTo\tInitial Temperature\n'.format(To),
            ' {}\tndimension\n'.format({'Arr':2,'dArr':3}[theory]),
            ' {}\t{}\t{}\n\n'.format(X_0[0],X_0[1],X_0[2])
            ]
        gsa_in = open('GSA.in','w')
        gsa_in.writelines(txt)
        gsa_in.close()

        ###########################################
        ### Execute

        if platform.system() == 'Windows':
            os.system('GSADriverWin.exe')
            try:
                os.system('del GSADriverLin.exe')
                os.system('del GSADriverMac.exe')
                os.system('del GetPermission.sh')
            except:
                pass

        if platform.system() == 'Linux':
            os.system('./GSADriverLin.exe')
            try:
                os.system('rm ./GSADriverWin.exe')
                os.system('rm ./GSADriverMac.exe')
            except:
                pass

        if platform.system() == 'Darwin':
            os.system('./GSADriverMac.exe')
            try:
                os.system('rm GSADriverWin.exe')
                os.system('rm GSADriverLin.exe')
            except:
                pass

        ###########################################
        ### Extract X_Min
        gsa_in = open('GSA.in','r')
        txt =  gsa_in.readlines()
        gsa_in.close()
        self.X_Min[theory] = [float(xmin) for xmin in txt[7].split()]

        ### Extract GraphicsFile.dat
        graphic_file = open('GraphicsFile.dat','r')
        txt = graphic_file.readlines()
        graphic_file.close()

        self.YFit[theory] = []
        self.XFit = []
        for n in range(1, len(txt)):
            self.XFit.append(float(txt[n].split()[0]))
            self.YFit[theory].append(float(txt[n].split()[2]))
        ### Extract Convergency.dat
        with open('Convergency.dat','r') as conv:
            txt = conv.readlines()


        ChiSq = []
        NCycle = []
        for ln in txt:
            ChiSq.append(float(ln.split()[5]))
            NCycle.append(float(ln.split()[6]))
        NCycle.append(N)
        ChiSq.append(ChiSq[-1])

        ###########################################
        ### Write parameters
        for ed, n in zip({'dArr':[0,1,2],'Arr':[3,4,2]}[theory],[0,1,2]):
            self.ed[ed].delete(0, END)
            self.ed[ed].insert(1, str(self.X_Min[theory][n]))
        if theory is 'Arr' and 'dArr' not in self.X_Min:
            for n in range(2):
                self.ed[n].delete(0, END)
                self.ed[n].insert(1, str(self.X_Min['Arr'][n]))

        if theory is 'dArr' and 'Arr' not in self.X_Min:
            for n,m in ((3,0),(4,1)):
                self.ed[n].delete(0, END)
                self.ed[n].insert(1, str(self.X_Min['dArr'][m]))


        self.ChiSq[theory]['text'] = ' Chi-square: {} '.format(ChiSq[-1])

        ###########################################
        ### Plot Convergency
        try:
            plt.plot(NCycle,ChiSq)
            plt.xticks([])
            plt.title('Convergency',fontsize='x-large')
            plt.ylabel('Chi-Square',fontsize='x-large')
            plt.tight_layout()
            plt.grid(True)
            plt.show()
        except:
            pass

    def Help(self):
        try:
            if platform.system() == 'Windows':
                os.startfile("ProgramHelp.pdf")
            if platform.system() == 'Linux':
                os.system('xdg-open ProgramHelp.pdf')
            if platform.system() == 'Darwin':
                os.system('open -a ProgramHelp.pdf')
        except:
            messagebox.showerror(title='Error',message='Please Download the manual at the address: https://github.com/hugoUnB/Qd10GSA')

    def About(self):
        t = Toplevel(self)
        t.geometry("600x120")
        #t.resizable(False, False)
        Label(t, text="\nProgram developed by Kleber C. Mundim e Hugo G. Machado. Version {}\n\nFor bug reports or questions, please email us at:\n\n hugogontijomachado@gmail.com or kcmundim@unb.br".format(self.__version__)).pack()

    def Exit(self):
        self.destroy()

if __name__ == "__main__":
    root = Fitting()
    root.mainloop()
