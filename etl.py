from pandas import DataFrame


class Conection:
    def __init__(self, server:str,database:str,driver:str):
        '''
        Class created to make de ETL process to get data needed to fill a Data warehouse.

        INPUT
        * server [str] = Expects a string with the server information to connect.
        * database [str] = Expects a string with the database information to connect.
        * driver [str] = Expects a string with the driver information to connect.

        OUTPUT (According to selected method)
        * get_finance_info().
        * get_sales_info().
        * get_inventory_info().

        '''
        self.server   = server
        self.database = database
        self.driver   = driver

    def cursor(self,query:str):
        '''
        Private method to execute a query to the conection.

        INPUT
        * query [str] = Expects a string with the query to be executed.

        OUTPUT
        * result [list] = Returns a list with the data returned from the execution of the query.
        '''
        # Define las credenciales de conexión
        server = 'LAP-DIEGO\SQLEXPRESS'#type:ignore
        database = 'Upysusa'
        driver = 'ODBC Driver 17 for SQL Server'

        # Conecta a la base de datos
        conection = pyodbc.connect(f'DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes')#Establece la conexion
        cursor = conection.cursor()
        result = cursor.execute(query).fetchall()
        conection.close()
        return result
    
    def get_finance_info(self, download:bool = False, verbose:bool = False):
        '''
        Public method to gather the needed information needed to answer the questions of the visualization for finance area.

        INPUT
        * download [bool] = Expects a bool which indicates if the finance_info should be downloaded as a JSON. Default is set to False.
        * verbose [bool] = Expects a bool which indicates if the process log should be displayed in console. Default is set to False.

        OUTPUT
        * finance_dict [dict of 'pandas.DataFrame' objects] = Returns a dict of 'pandas.DataFrame' objects with the information needed to answer 'p)' in Finance scopes.
        '''
        
        def get_dictionary(data_table:DataFrame, verbose:bool = False):
            '''
            Private function to generate a dictionary that contains the information of 'data_table'

            INPUT
            * data_table [pandas.DataFrame] = Expects a 'pandas.DataFrame' object that must have a column with the following names:
                * NOMBRE_SUCURSAL
                * ANO 
                * MES
                * DIA
                * MONTO
            * verbose [bool] = Expects a bool which indicates if the process log should be displayed in console. Default is set to False.

            OUTPUT
            * detalle_scope [dict] = Returns a dict with the information of 'data_table' summarized and organized
            '''
            if verbose: print(f"Generando JSON...")
            # New Level
            detalle_scope = {}
            for sucursal in sorted(set(data_table['NOMBRE_SUCURSAL'])):
                # Data
                data_sucursal = data_table.query(f"NOMBRE_SUCURSAL == '{sucursal}'")
                detalle_sucursal = {'Total Ventas Sucursal' : sum(data_sucursal['MONTO'])}
                # New Level - year
                for year in sorted(set(data_sucursal['ANO'])):
                    # Data
                    data_years = data_sucursal.query(f"ANO == {year}")
                    detalle_years = {'Total Ventas Anual' : sum(data_years['MONTO'])}
                    # New Level - Trimestre
                    for trimester in range(3,13,3):
                        # Data
                        data_trimestre = data_years.query(f"MES>={trimester-2} & MES <={trimester}")
                        detalle_trimestre = {'Total Ventas Trimestral' : sum(data_trimestre['MONTO'])}
                        # New Level - Mes
                        for mes in sorted(set(data_trimestre['MES'])):
                            # Data
                            data_mes = data_trimestre.query(f"MES == {mes}")
                            detalle_mes = {'Total Ventas Mensual' : sum(data_mes['MONTO'])}
                            # New Level - semana
                            for semana in range(1,6):
                                # Data
                                data_semana = data_mes.query(f"DIA>={(semana*7)-6} & DIA<={semana*7}")
                                detalle_semana = {'Total Ventas Semanal' : sum(data_semana['MONTO'])}
                                # New Leve - Dia
                                for dia in sorted(set(data_semana['DIA'])):
                                    # Data
                                    data_dia = data_semana.query(f"DIA == {dia}")
                                    
                                    # Maping Data - Dia
                                    detalle_semana[dia] = sum(data_dia['MONTO'])
                                # Maping - Semana
                                detalle_mes[f"S{semana}"] = detalle_semana #type:ignore
                            # Maping - Mes
                            detalle_trimestre[f"{mes}M"] = detalle_mes #type:ignore
                        # Maping - Trimestre
                        detalle_years[f"{int(trimester/3)}"] = detalle_trimestre #type:ignore
                    # Maping trimeste_dic to a property
                    detalle_sucursal[year] = detalle_years #type:ignore
                # Maping dic_years to a property
                detalle_scope[sucursal] = detalle_sucursal
            if verbose: print(f"JSON generado!\n")
            return detalle_scope

        # GASTOS
        if verbose: print(f"{'*'*15} SELECCIONANDO INFORMACION PARA FINANZAS {'*'*15}\nGenerando relacion Sucursal - Gastos\n")
        row_data = self.cursor("SELECT GASTOS.ID_SUCURSAL,CATALOGO_GASTOS.NOMBRE,GASTOS.MONTO,GASTOS.DIA,GASTOS.MES,GASTOS.ANO,SUCURSALES.COLONIA FROM GASTOS INNER JOIN CATALOGO_GASTOS ON GASTOS.ID_NOMBRE_GASTO = CATALOGO_GASTOS.ID_NOMBRE_GASTO INNER JOIN SUCURSALES ON GASTOS.ID_SUCURSAL = SUCURSALES.ID_SUCURSAL ORDER BY GASTOS.ID_SUCURSAL ASC")
        data_table = pd.DataFrame(data = {
            'ID_SUCURSAL'     : [row[0]              for row in row_data],
            'NOMBRE_SUCURSAL' : [F"Upysusa {row[6]}" for row in row_data],
            'NOMBRE_GASTO'    : [row[1]              for row in row_data],
            'MONTO'           : [row[2]              for row in row_data],
            'DIA'             : [row[3]              for row in row_data],
            'MES'             : [row[4]              for row in row_data],
            'ANO'             : [row[5]              for row in row_data],
        })
        if verbose: print(f"Data seleccionada\n{data_table.head()}")
        sucursal_gastos = get_dictionary(data_table=data_table, verbose=verbose)

        # COMPRAS
        if verbose: print(f"\n\nGenerando relacion Sucursal - Compras")
        row_data = self.cursor("SELECT COLONIA AS NOMBRE_SUCURSAL, ID_COMPRA, RAZON_SOCIAL, NO_PRODUCTOS, COSTO_TOTAL_PEDIDO, COMPRAS.DIA, COMPRAS.MES, COMPRAS.ANO FROM COMPRAS INNER JOIN SUCURSALES ON COMPRAS.ID_SUCURSAL = SUCURSALES.ID_SUCURSAL INNER JOIN PROVEEDORES ON COMPRAS.ID_PROVEEDOR = PROVEEDORES.ID_PROVEEDOR ORDER BY COMPRAS.ID_SUCURSAL ASC")
        data_table = pd.DataFrame(data={
            'NOMBRE_SUCURSAL' : [row[0] for row in row_data] ,
            'ID_COMPRA'       : [row[1] for row in row_data] ,
            'RAZON_SOCIAL'    : [row[2] for row in row_data] ,
            'NO_PRODUCTOS'    : [row[3] for row in row_data] ,
            'MONTO'           : [row[4] for row in row_data] ,
            'DIA'             : [row[5] for row in row_data] ,
            'MES'             : [row[6] for row in row_data] ,
            'ANO'             : [row[7] for row in row_data] 
        })
        if verbose: print(f"Data seleccionada\n{data_table.head()}")
        sucursal_compras = get_dictionary(data_table=data_table, verbose=verbose)
        
        # VENTAS
        if verbose: print(f"\n\nGenerando relacion Sucursal - Ventas")
        row_data = self.cursor("SELECT TICKETS.ID_TICKET, EMPLEADOS.APELLIDO_PAT, EMPLEADOS.NOMBRE, SUCURSALES.COLONIA, TICKETS.FECHA, TOTAL_COMPRA FROM TICKETS  INNER JOIN SUCURSALES ON SUCURSALES.ID_SUCURSAL = TICKETS.ID_SUCURSAL INNER JOIN EMPLEADOS ON EMPLEADOS.ID_SUCURSAL = SUCURSALES.ID_SUCURSAL ORDER BY TICKETS.ID_SUCURSAL ASC")
        data_table = pd.DataFrame(data={
            'ID_TICKET'       : [row[0]                for row in row_data] ,
            'NOMBRE_EMPLEADO' : [F"{row[1]}, {row[2]}" for row in row_data] ,
            'NOMBRE_SUCURSAL' : [F"Upysusa {row[3]}"   for row in row_data] ,
            'DIA'             : [row[4].day            for row in row_data] ,
            'MES'             : [row[4].month          for row in row_data] ,
            'ANO'             : [row[4].year           for row in row_data] ,
            'MONTO'           : [row[5]                for row in row_data] 
        })
        if verbose: print(f"Data seleccionada\n{data_table.head()}")
        sucursal_ventas = get_dictionary(data_table=data_table, verbose=verbose)


        finance_dict = {
            'Gastos - Sucursal'  : sucursal_gastos,
            'Compras - Sucursal' : sucursal_compras,
            'Ventas - Sucursal'  : sucursal_ventas
        }
        if download: json.dump(finance_dict,open('finance_info.json','w'))
        return finance_dict

    def get_inventory_info(self, download:bool = False, verbose:bool = False):
        '''
        Public method to gather the needed information needed to answer the questions of the visualization for inventory area.

        INPUT
        * download [bool] = Expects a bool which indicates if the finance_info should be downloaded as a JSON. Default is set to False.
        * verbose [bool] = Expects a bool which indicates if the process log should be displayed in console. Default is set to False.

        OUTPUT
        * inventory_dict [dict of 'pandas.DataFrame' objects] = Returns a dict of 'pandas.DataFrame' objects with the information needed to answer 'p)' in Inventory scopes.
        '''
        if verbose: print(f"{'*'*15} SELECCIONANDO INFORMACION PARA INVENTARIO {'*'*15}\nGenerando relacion Sucursal - Productos\n")
        row_data = self.cursor("SELECT COLONIA AS NOMBRE_SUCURSAL,ALMACEN_POR_SUCURSAL.ID_SUCURSAL,COMPRA_POR_PRODUCTO.ID_PRODUCTO,PRODUCTOS.NOMBRE,PRODUCTOS.CATEGORIA FROM ALMACEN_POR_SUCURSAL INNER JOIN COMPRA_POR_PRODUCTO ON COMPRA_POR_PRODUCTO.ID_COMPRA = ALMACEN_POR_SUCURSAL.ID_COMPRA INNER JOIN SUCURSALES ON ALMACEN_POR_SUCURSAL.ID_SUCURSAL = SUCURSALES.ID_SUCURSAL INNER JOIN PRODUCTOS ON COMPRA_POR_PRODUCTO.ID_PRODUCTO = PRODUCTOS.ID_PRODUCTO ORDER BY ALMACEN_POR_SUCURSAL.ID_SUCURSAL ASC")
        data_table = pd.DataFrame(data={
            "NOMBRE_SUCURSAL"    : [f'Upysusa {row[0]}' for row in row_data],
            "ID_SUCURSAL"        : [row[1] for row in row_data],
            "ID_PRODUCTO"        : [row[2] for row in row_data],
            "NOMBRE_PRODUCTO"    : [row[3] for row in row_data],
            "CATEGORIA_PRODUCTO" : [row[4] for row in row_data]
        })
        if verbose: print(f"Generando JSON...")
        sucursal_productos = {}
        # New Level
        for sucursal in sorted(set(data_table['NOMBRE_SUCURSAL'])):
            # Data
            data_sucursal = data_table.query(f"NOMBRE_SUCURSAL == '{sucursal}'")
            detalle_sucursal = {
                'Total Productos'  : len(set(data_sucursal['NOMBRE_PRODUCTO'])),
                'Total Categorias' : len(set(data_sucursal['CATEGORIA_PRODUCTO']))
            }
            # Nested data - categoria
            for categoria in sorted(set(data_sucursal['CATEGORIA_PRODUCTO'])):
                # Data
                data_categoria = data_sucursal.query(f"CATEGORIA_PRODUCTO == '{categoria}'")
                detalle_categoria = {
                    'Total Productos' : len(set(data_categoria['ID_PRODUCTO'])),
                    'Lista Productos' : list(set(data_categoria['NOMBRE_PRODUCTO']))
                }
                # Mapping details
                detalle_sucursal[categoria] = detalle_categoria #type:ignore
            # Mapping details
            sucursal_productos[sucursal] = detalle_sucursal
        if verbose: print('JSON Generado!\n')


        if verbose: print(f"\nGenerando relacion Fecha Compra - Fecha Recibido\n")
        row_data = self.cursor("SELECT CPP.ID_COMPRA, CPP.ID_PRODUCTO, PRD.CATEGORIA AS CATEGORIA_PRODUCTO,PRD.NOMBRE AS NOMBRE_PRODUCTO, PRD.ID_PROVEEDOR,PRV.RAZON_SOCIAL,CPP.DIA_COMPRA, CPP.MES_COMPRA, CPP.ANO_COMPRA,APS.TS_INGRESO FROM COMPRA_POR_PRODUCTO CPP INNER JOIN ALMACEN_POR_SUCURSAL APS ON CPP.ID_COMPRA = APS.ID_COMPRA INNER JOIN PRODUCTOS AS PRD ON CPP.ID_PRODUCTO = PRD.ID_PRODUCTO INNER JOIN PROVEEDORES AS PRV ON PRD.ID_PROVEEDOR = PRV.ID_PROVEEDOR")
        data_table = pd.DataFrame(data={
            "ID_COMPRA"          : [row[0]         for row in row_data],
            "ID_PRODUCTO"        : [row[1]         for row in row_data],
            "NOMBRE_PRODUCTO"    : [row[2]         for row in row_data],
            "CATEGORIA_PRODUCTO" : [row[3]         for row in row_data],
            "DIA_COMPRA"         : [row[4]         for row in row_data],
            "MES_COMPRA"         : [row[5]         for row in row_data],
            "ANO_COMPRA"         : [row[6]         for row in row_data],
            "DIA_INGRESO"        : [row[7].day     for row in row_data],
            "MES_INGRESO"        : [row[7].month   for row in row_data],
            "ANO_INGRESO"        : [row[7].year    for row in row_data]
        })
        if verbose: print(f"Generando JSON...\n{data_table.head()}")

        FechaCompra_FechaRecibo = {}
        # New Level
        for categoria in sorted(set(data_table['CATEGORIA_PRODUCTO'])):
            # Data
            data_categoria = data_table.query(f"CATEGORIA_PRODUCTO == '{categoria}'")
            detalle_categoria = {}

        FechaIngreso_FechaVenta = {}
        
        

        inventory_dict = {
            'Relacion Sucursal - Productos'                               : sucursal_productos,
            'Relacion de Fecha Ingreso Producto - Fecha Venta Producto'   : FechaIngreso_FechaVenta,
            'Relacion de Fecha Compra Producto - Fecha Recibido Producto' : FechaCompra_FechaRecibo
        }
        if download: json.dump(inventory_dict,open('inventory_info.json','w'))
        return inventory_dict
    
    def get_sales_info(self, download:bool = False, verbose:bool = False):
        '''
        Public method to gather the needed information needed to answer the questions of the visualization for sales area.

        INPUT
        * download [bool] = Expects a bool which indicates if the finance_info should be downloaded as a JSON. Default is set to False.
        * verbose [bool] = Expects a bool which indicates if the process log should be displayed in console. Default is set to False.

        OUTPUT
        * sales_dict [dict of 'pandas.DataFrame' objects] = Returns a dict of 'pandas.DataFrame' objects with the information needed to answer 'p)' in Sales scopes.
        '''
        tickets_empleado = pd.DataFrame()
        tickets_producto = pd.DataFrame()
        


        sales_dict = {
            'Relacion Tickets - Empleado' : tickets_empleado,
            'Relacion Tickets - Producto' : tickets_producto
        }
        return sales_dict


    
if __name__ == '__main__':
    import os; os.system('cls')
    import pandas as pd
    from sqlalchemy import create_engine
    import pyodbc, chardet, platform, json, calendar

    # Define las credenciales de conexión
    server = 'LAP-DIEGO\SQLEXPRESS'#type:ignore
    database = 'Upysusa'
    driver = 'ODBC Driver 17 for SQL Server'

    conection = Conection(
        server   = server,
        database = database,
        driver   = driver
    )

    conection.get_inventory_info(
        download = True,
        verbose = True
    ).get