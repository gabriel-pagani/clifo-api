import flet as ft
import re
import datetime
import asyncio
import json
import os
from utils.ui import show_message
from utils.validator import is_valid_cnpj
from apis.receitaws import cnpj_lookup
from apis.customer_vendor import create_new_customer_vendor
from database.connection import execute_query


class HomeView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.customers_vendors = dict()
    
    def show(self):
        def update_list_of_cnpjs():
            list_of_cnpjs.controls.clear()
            for cnpj, data in self.customers_vendors.items():
                list_of_cnpjs.controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.BUSINESS, color=ft.Colors.GREY_900),
                                ft.Column(
                                    controls=[
                                        ft.Text(f"Cnpj: {cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}", weight="bold"),
                                        ft.Text(f"Tipo: {"Cliente" if data["type"] == "c" else ("Fornecedor" if data["type"] == "f" else "Ambos")} | IE: {data["ie"]}" if data["ie"] else f"Tipo: {"Cliente" if data["type"] == "c" else ("Fornecedor" if data["type"] == "f" else "Ambos")}")
                                    ], 
                                    expand=True
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ft.Colors.RED,
                                    tooltip="Remover cnpj",
                                    on_click=lambda e, cj=cnpj: remove_cnpj_from_list(cj)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=10,
                        border=ft.Border.all(1, ft.Colors.GREY_300),
                        border_radius=5
                    )
                )

            self.page.update()

        def on_cnpj_input_change(e):
            new_value = re.sub(r"\D", "", cnpj_input.value or "")
            if cnpj_input.value != new_value:
                cnpj_input.value = new_value
                cnpj_input.update()

        def on_ie_input_change(e):
            new_value = re.sub(r"[^A-Za-z0-9]", "", ie_input.value or "")
            if ie_input.value != new_value:
                ie_input.value = new_value
                ie_input.update()

        def add_cnpj_to_list(e):
            cnpj_input.error = None
            ie_input.error = None
            type_input.error_text = None
            
            has_error = False

            raw_cnpj = (cnpj_input.value or "").strip()
            cnpj_digits = re.sub(r"\D", "", raw_cnpj)

            raw_ie = (ie_input.value or "").strip()
            ie_digits = re.sub(r"\D", "", raw_ie)
            ie_sanitized = "isento" if raw_ie.lower() == "isento" else ie_digits

            if not cnpj_digits:
                cnpj_input.error = "Campo obrigatório!"
                has_error = True

            if cnpj_digits and cnpj_digits in self.customers_vendors:
                cnpj_input.error = "Esse cnpj já foi adicionado!"
                has_error = True

            if cnpj_digits and not is_valid_cnpj(cnpj_digits):
                cnpj_input.error = "Cnpj inválido!"
                has_error = True

            if ie_sanitized and ie_sanitized != "isento":
                if not ie_sanitized.isdigit():
                    ie_input.error = "Inscrição estadual inválida!"
                    has_error = True
                else:
                    if any((re.sub(r"\D", "", (item.get("ie") or "")) == ie_sanitized)
                           for item in self.customers_vendors.values()):
                        ie_input.error = "Essa inscrição estadual já foi utilizada!"
                        has_error = True

            if not type_input.value:
                type_input.error_text = "Campo obrigatório!"
                has_error = True

            if has_error:
                cnpj_input.update()
                ie_input.update()
                type_input.update()
                return

            self.customers_vendors[cnpj_digits] = {
                "ie": ie_sanitized,
                "type": type_input.value
            }
            
            cnpj_input.value = ""
            ie_input.value = ""
            
            update_list_of_cnpjs()
            show_message(self.page, 1, "Cnpj adicionado com sucesso!")

        async def import_cnpjs_to_list(e):
            try:
                file = await ft.FilePicker().pick_files(
                    initial_directory=os.path.join(os.path.abspath(""), "src", "assets"),
                    file_type=ft.FilePickerFileType.CUSTOM, 
                    allowed_extensions=["json"], 
                    allow_multiple=False
                )

                if not file:
                    return
                
                with open(file[0].path, "r", encoding="utf-8") as f:
                    cnpjs_list = json.load(f)
                    
                self.customers_vendors = cnpjs_list
                update_list_of_cnpjs()
                show_message(self.page, 1, "Lista de cnpjs importada com sucesso!")

            except Exception as e:
                show_message(self.page, 3, f"Erro ao importar lista de cnpjs: {e}")
                return

        def remove_cnpj_from_list(cnpj):
            if cnpj in self.customers_vendors:
                del self.customers_vendors[cnpj]
                update_list_of_cnpjs()
                show_message(self.page, 1, "Cnpj removido com sucesso!")

        def disable_ui():
            cnpj_input.disabled = True
            ie_input.disabled = True
            type_input.disabled = True
            add_cnpj_button.disabled = True
            add_cnpj_button.icon_color = ft.Colors.GREY_300
            add_cnpj_button.tooltip = "Automação em execução!"
            import_cnpjs_button.disabled = True
            import_cnpjs_button.icon_color = ft.Colors.GREY_300
            import_cnpjs_button.tooltip = "Automação em execução!"
            start_automation_button.disabled = True
            start_automation_button.tooltip = "Automação em execução!"

            for container in list_of_cnpjs.controls:
                container.content.controls[2].disabled = True
                container.content.controls[2].icon_color = ft.Colors.GREY_300
                container.content.controls[2].tooltip = "Automação em execução!"
            
            self.page.update()

        def enable_ui():
            cnpj_input.disabled = False
            ie_input.disabled = False
            type_input.disabled = False
            add_cnpj_button.disabled = False
            add_cnpj_button.icon_color = ft.Colors.GREEN
            add_cnpj_button.tooltip = "Adicionar cnpj"
            import_cnpjs_button.disabled = False
            import_cnpjs_button.icon_color = ft.Colors.BLUE
            import_cnpjs_button.tooltip = "Importar lista de cnpjs"
            start_automation_button.disabled = False
            start_automation_button.tooltip = None

            for container in list_of_cnpjs.controls:
                container.content.controls[2].disabled = False
                container.content.controls[2].icon_color = ft.Colors.RED
                container.content.controls[2].tooltip = "Remover cnpj"
        
        def add_log(message: str, type: str = "info"):
            now = datetime.datetime.now().strftime("%H:%M:%S")
            color = ft.Colors.BLACK
            
            if type == "success":
                color = ft.Colors.GREEN
            elif type == "warning":
                color = ft.Colors.ORANGE
            elif type == "error":
                color = ft.Colors.RED
            
            logs.controls.append(
                ft.Text(f"[{now}] {message}", color=color, selectable=True, size=14)
            )
            logs.scroll_to(offset=-1, duration=1000)
            logs.update()
        
        async def run_automation_tesk():
            add_log("Iniciando automação...", "info")
            await asyncio.sleep(0.1)
            
            len_customers_vendors = len(self.customers_vendors)

            if len_customers_vendors > 3:
                total_seconds = len_customers_vendors * 24

                hours = total_seconds // 3600
                remaining_seconds = total_seconds % 3600
                minutes = remaining_seconds // 60
                seconds = remaining_seconds % 60

                parts = []

                if hours > 0:
                    parts.append(f"{hours} hora" if hours == 1 else f"{hours} horas")

                if minutes > 0:
                    parts.append(f"{minutes} minuto" if minutes == 1 else f"{minutes} minutos")

                if seconds > 0 or not parts:
                    parts.append(f"{seconds} segundo" if seconds == 1 else f"{seconds} segundos")

                duration_text = " e ".join(parts)

                add_log(f"Duração prevista: {duration_text}", "info")
            else:
                add_log(f"Duração prevista: 10 segundos", "info")
            await asyncio.sleep(0.1)

            for i, (cnpj, infos) in enumerate(self.customers_vendors.items()):
                formatted_cnpj = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
                
                if infos["type"].lower() == "c":
                    add_log(f"Cadastrando o cliente {formatted_cnpj}...", "info")
                elif infos["type"].lower() == "f":
                    add_log(f"Cadastrando o fornecedor {formatted_cnpj}...", "info")
                await asyncio.sleep(0.1)
                
                
                cnpj_exists = execute_query("SELECT TOP 1 CODCFO FROM FCFO WHERE CODCOLIGADA IN (1,5,6) AND CGCCFO = ?", (formatted_cnpj,))
                if cnpj_exists:
                    if infos["type"].lower() == "c":
                        add_log(f"O cliente {formatted_cnpj} já está cadastrado! CODCFO: {cnpj_exists[0][0]}", "info")
                    elif infos["type"].lower() == "f":
                        add_log(f"O fornecedor {formatted_cnpj} já está cadastrado! CODCFO: {cnpj_exists[0][0]}", "info")
                    await asyncio.sleep(0.1)
                    continue
                
                try:
                    data = execute_query("""
                        SELECT
                            'F' + RIGHT('00000' + CAST((CAST(SUBSTRING((SELECT TOP 1 CODCFO FROM FCFO WHERE CODCFO LIKE 'F%' AND CODCOLIGADA in (1,5,6) ORDER BY CODCFO DESC), 2, 5) AS INT) + 1) AS VARCHAR), 5) AS COD_FOR,
                            'C' + RIGHT('00000' + CAST((CAST(SUBSTRING((SELECT TOP 1 CODCFO FROM FCFO WHERE CODCFO LIKE 'C%' AND CODCOLIGADA in (1,5,6) ORDER BY CODCFO DESC), 2, 5) AS INT) + 1) AS VARCHAR), 5) AS COD_CLI,
                            'A' + RIGHT('00000' + CAST((CAST(SUBSTRING((SELECT TOP 1 CODCFO FROM FCFO WHERE CODCFO LIKE 'A%' AND CODCOLIGADA in (1,5,6) ORDER BY CODCFO DESC), 2, 5) AS INT) + 1) AS VARCHAR), 5) AS COD_CLIFOR
                    """)
                    codcfo = data[0][0] if infos["type"].lower() == "f" else (data[0][1] if infos["type"].lower() == "c" else data[0][2])
                    
                    resp = cnpj_lookup(codcfo=codcfo, cnpj=cnpj, ie=infos["ie"])
                    
                    if resp["status"].upper() != "ATIVA":
                        raise Exception(f"CNPJ com situação irregular")

                    for idx in ["1", "5", "6"]:
                        create_new_customer_vendor(
                            companyId=idx,
                            code=resp["code"],
                            shortName=resp["shortName"],
                            name=resp["name"],
                            type=resp["type"],
                            mainNIF=resp["mainNIF"],
                            stateRegister=resp["stateRegister"],
                            zipCode=resp["zipCode"],
                            streetType=resp["streetType"],
                            streetName=resp["streetName"],
                            number=resp["number"],
                            districtType=resp["districtType"],
                            district=resp["district"],
                            stateCode=resp["stateCode"],
                            cityInternalId=resp["cityInternalId"],
                            phoneNumber=resp["phoneNumber"],
                            email=resp["email"],
                            contributor=resp["contributor"]
                        )

                    execute_query(
                        "UPDATE FCFO SET CONTRIBUINTE = ?, COMPLEMENTO = ? WHERE CODCOLIGADA IN (1,5,6) AND CGCCFO = ?", 
                        (
                            resp["contributor"], 
                            resp["complement"] if resp["complement"] else None, 
                            formatted_cnpj
                        )
                    )

                    if infos["type"].lower() == "c":
                        add_log(f"Sucesso ao cadastrar o cliente {cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}! CODCFO: {codcfo}", "success")
                    elif infos["type"].lower() == "f":
                        add_log(f"Sucesso ao cadastrar o fornecedor {cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}! CODCFO: {codcfo}", "success")

                except Exception as e:
                    if infos["type"].lower() == "c":
                        add_log(f"Erro ao cadastrar o cliente {cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}! ERRO: {e}", "error")
                    elif infos["type"].lower() == "f":
                        add_log(f"Erro ao cadastrar o fornecedor {cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}! ERRO: {e}", "error")
                
                await asyncio.sleep(0.1)
                
                if len_customers_vendors > 3 and i < len_customers_vendors - 1:
                    add_log("Aguardando 20s...", "info")
                    await asyncio.sleep(20)

            enable_ui()

            self.customers_vendors = dict()
            update_list_of_cnpjs()
            
            self.page.update()
            add_log("Automação finalizada!", "success")
            await asyncio.sleep(0.1)
        
        def start_automation(e):
            if not self.customers_vendors:
                show_message(self.page, 2, "A lista de cnpjs está vazia!")
                return
            
            disable_ui()
            
            self.page.run_task(run_automation_tesk)


        # Components
        cnpj_input = ft.TextField(
            label="CNPJ",
            expand=True,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.GREY_300,
            on_change=on_cnpj_input_change,
            on_submit=add_cnpj_to_list,
        )

        ie_input = ft.TextField(
            label="IE",
            expand=True,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.GREY_300,
            on_change=on_ie_input_change,
            on_submit=add_cnpj_to_list,
        )

        type_input = ft.Dropdown(
            label="Tipo",
            width=200,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.GREY_300,
            options=[
                ft.dropdown.Option("c", "Cliente"),
                ft.dropdown.Option("f", "Fornecedor"),
                # ft.dropdown.Option("a", "Ambos"),
            ]
        )

        add_cnpj_button = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE,
            icon_color=ft.Colors.GREEN,
            icon_size=40,
            tooltip="Adicionar cnpj",
            on_click=add_cnpj_to_list,
        )

        import_cnpjs_button = ft.IconButton(
            icon=ft.Icons.UPLOAD_FILE_ROUNDED,
            icon_color=ft.Colors.BLUE,
            icon_size=40,
            tooltip="Importar lista de cnpjs",
            on_click=import_cnpjs_to_list,
        )

        start_automation_button = ft.Button(
            content=ft.Text("Iniciar automação"),
            height=50,
            bgcolor=ft.Colors.GREY_900,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=start_automation,
        )

        list_of_cnpjs = ft.ListView(
            expand=True, 
            spacing=10
        )
        
        logs = ft.ListView(
            expand=True, 
            spacing=5, 
            auto_scroll=True
        )

        
        # Layout
        cnpj_form = ft.Row(
            controls=[
                cnpj_input,
                ie_input,
                type_input,
                add_cnpj_button,
                import_cnpjs_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )

        column = ft.Column(
            controls=[
                ft.Container(
                    content=cnpj_form,
                    padding=10,
                    bgcolor=ft.Colors.TRANSPARENT,
                    border_radius=10
                ),
                ft.Text("Clientes/Fornecedores:", size=16, weight="bold", color=ft.Colors.GREY_900),
                ft.Container(
                    content=list_of_cnpjs,
                    expand=True,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    padding=5
                ),
                ft.Text("Logs:", size=16, weight="bold", color=ft.Colors.GREY_900),
                ft.Container(
                    content=logs,
                    expand=True,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    padding=10
                ),
                ft.Container(
                    content=start_automation_button,
                    padding=ft.Padding.only(top=10)
                ),
            ],
            expand=True
        )

        container = ft.Container(
            content=column,
            padding=20,
            expand=True
        )

        self.page.clean()
        self.page.add(container)
