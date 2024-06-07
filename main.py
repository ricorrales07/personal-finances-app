# -*- coding: utf-8 -*-
"""
Created on Fri Dec 22 20:57:31 2023

@author: Ricardo Corrales Barquero
"""

import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QDialog, \
    QTableWidgetItem
from PyQt5.QtCore import pyqtSlot, Qt, QDate
from ui_ventanaPrincipal import Ui_ventanaPrincipal
from ui_dlg_importar import Ui_dlg_importar
import sys
import pandas as pd
from datetime import datetime

__version__ = "0.0.0"
COLUMNA_CATEGORIA = 6

def llenar_tabla(table_widget, df):
    
    table_widget.setRowCount(len(df))
    table_widget.setColumnCount(len(df.columns))
    
    for i, fila in df.iterrows():
        for j, (_, valor) in enumerate(fila.items()):
            item = QTableWidgetItem(str(valor))
            table_widget.setItem(i, j, item)
            
    table_widget.setHorizontalHeaderLabels(df.columns)
    
    table_widget.resizeColumnsToContents()

class Dlg_Importar(QDialog, Ui_dlg_importar):
    
    def __init__(self, df, parent=None):
        super(Dlg_Importar, self).__init__(parent)
        
        self.setupUi(self)
        
        self.df = df
        llenar_tabla(self.tw_datos, df)
        
    @pyqtSlot(int, int)
    def on_tw_datos_cellDoubleClicked(self, fila, columna):
        
        if columna != COLUMNA_CATEGORIA:
            self.tw_datos.item(fila, columna).setFlags(self.tw_datos.item(fila, columna).flags() & ~Qt.ItemIsEditable)

    @pyqtSlot(int, int)
    def on_tw_datos_cellChanged(self, fila, columna):
        valor = self.tw_datos.item(fila, columna).data(Qt.DisplayRole)
        
        tipo = type(self.df.iloc[fila, columna])
        valor = tipo(valor)
        
        self.df.iloc[fila, columna] = valor

class VentanaPrincipal(QMainWindow, Ui_ventanaPrincipal):
    
    def __init__(self, parent=None):
        super(VentanaPrincipal, self).__init__(parent)
        
        self.df = None
        
        self.setupUi(self)
        
        self.dte_mes.setDate(datetime.now())
        
    @pyqtSlot()
    def on_actionArchivo_de_movimientos_del_Banco_Nacional_triggered(self):
        nombre_archivo, _ = QFileDialog.getOpenFileName(self, "Abrir archivo",
                                       ".",
                                       "*.csv")
        
        saldosBN1 = pd.read_csv(nombre_archivo, sep=';', 
                        usecols=['oficina', 'fechaMovimiento', 'numeroDocumento', 'debito', 'credito', 'descripcion'],
                        dtype={'oficina': int, 
                               'numeroDocumento': str, 
                               'descripcion': str},
                        skipfooter=1)
        
        saldosBN1['fechaMovimiento'] = pd.to_datetime(saldosBN1['fechaMovimiento'], format="%d/%m/%Y")
        
        saldosBN1['debito'][saldosBN1['debito'].isna()] = 0
        saldosBN1['debito'] = saldosBN1['debito'].apply(lambda x: float(x.replace(',', '')) if isinstance(x, str) else x)
        
        saldosBN1['credito'][saldosBN1['credito'].isna()] = 0
        saldosBN1['credito'] = saldosBN1['credito'].apply(lambda x: float(x.replace(',', '')) if isinstance(x, str) else x)
        
        saldosBN1['categoria'] = 'Otros gastos'
        
        saldosBN1.rename(columns={'fechaMovimiento': 'fechaRegistro'}, inplace=True)
        
        parseados = saldosBN1.apply(lambda fila: VentanaPrincipal.parse_descripcion(fila['fechaRegistro'], fila['descripcion'], fila['debito']), axis=1)
        parseadosDf = pd.DataFrame(parseados.tolist(), index=parseados.index, columns=['fechaMovimiento', 'descripcion'])
        saldosBN1[['fechaMovimiento', 'categoria']] = parseadosDf
        
        print(saldosBN1['debito'])
        
        dlg_importar = Dlg_Importar(saldosBN1)
        respuesta = dlg_importar.exec_()
        
        if respuesta == QDialog.Accepted:
            self.df = dlg_importar.df
            self.actualizarUi()
            
    @pyqtSlot(QDate)
    def on_dte_mes_userDateChanged(self, _):
        self.actualizarUi()
            
    def actualizarUi(self):
        fecha_seleccionada = self.dte_mes.date()
        
        if self.df is not None:
            resumen = self.df[(self.df['fechaMovimiento'].dt.month == fecha_seleccionada.month()) & (self.df['fechaMovimiento'].dt.year == fecha_seleccionada.year())][['categoria', 'debito']].groupby('categoria').sum()
            
            llenar_tabla(self.tw_gastos, resumen.reset_index())
            
            self.wgt_grafico.axes.cla()
            resumen.plot.pie(y='debito', ax=self.wgt_grafico.axes)
            #self.wgt_grafico.axes.plot([1, 2, 3], [8, 4, 5])
            self.wgt_grafico.draw()
        
    @staticmethod
    def parse_descripcion(fecha, descripcion, debito):
    
        try:
            dia = int(descripcion[:2])
            mes = int(descripcion[3:5])
            anno = 2000 + int(descripcion[6:8])
            descripcion = descripcion[8:]
        except ValueError:
            try:
                dia = int(descripcion[:2])
                mes = int(descripcion[3:5])
                anno = 2000 + int(descripcion[6:10])
                descripcion = descripcion[10:]
            except ValueError:
                return fecha, "Otros gastos"
            
        fecha = datetime(anno, mes, dia)
        
        if "UBER BV" in descripcion:
            return fecha, "Transporte"
        elif "UBERBV EATS" in descripcion:
            return fecha, "Comida"
        elif "THE SPOT" in descripcion or "AUTO MERCADO" in descripcion:
            return fecha, "Diario"
        elif "TRU VICE" in descripcion:
            return fecha, "Suscripciones"
        elif "SALARIO PLANILLA BANCO NACIONAL" in descripcion:
            return fecha, "Salario BN"
        elif debito == 0:
            return fecha, "Otros ingresos"
        else:
            return fecha, "Otros gastos"
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = VentanaPrincipal()
    
    main_window.show()
    app.exec_()