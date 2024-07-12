from rich import print as po
from rich.live import Live
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table
from rich.align import Align
from rich import box

from pyfiglet import figlet_format

# to plot terminal charts
import asciichartpy as acp

import random

import arts

import requests as req

import datetime as dt

import psutil
import platform
import cpuinfo



# some custom functions used throughout the app
def truncate_list(list_:list,
                  length:int):
    """
    Returns list_ with length = length
    """

    if len(list_) > length:
        list_ = list_[1:]
        return list_
    else:
        return list_
    
def greater_than(val_1:int, val_2:int):
    """function that returns val_1 if it is greater than val_2, else returns val_2"""
    if val_1 > val_2:
        return val_1
    else:
        return val_2

def random_arter():
    art_list = [v for v in dir(arts) if not v.startswith("__")]

    return random.choice(art_list)



# main backend function that gets all the required info
# will iterate over this continously, refreshing the system informations
def basic_info():
    # basic system info
    info_dict = {}
    info_dict["arch"] = platform.architecture()
    info_dict["net_name"] = platform.node()
    info_dict["os"] = platform.platform()
    info_dict["system"] = platform.system()
    info_dict["boot_time"] = dt.datetime.fromtimestamp(psutil.boot_time()).strftime("%d/%m/%Y, %H:%M:%S")
    info_dict["users"] = [i.name for i in psutil.users()] if [i.name for i in psutil.users()] != [] else "_______"

    return info_dict

def cpu_info():
    # CPU info
    cpu = cpuinfo.get_cpu_info()
    info_dict = {}
    info_dict["cpu"] = {}
    info_dict["cpu"]["name"] = cpu["brand_raw"]
    info_dict["cpu"]["arch"] = cpu["arch"]
    info_dict["cpu"]["clock_speed"] = cpu["hz_actual_friendly"]
    info_dict["cpu"]["stats"] = {}
    info_dict["cpu"]["stats"]["cores"] = psutil.cpu_count()
    info_dict["cpu"]["stats"]["percent_used"] = psutil.cpu_percent()
    info_dict["cpu"]["stats"]["times"] = [i[0] for i in psutil.cpu_times(percpu=True)]
    # support for windows since psutil doesnt have indivisual cpu speeds on windows
    if basic_info()["system"] != "Windows":
        info_dict["cpu"]["stats"]["speeds"] = [i[0] for i in psutil.cpu_freq(percpu=True)]
    else:
        info_dict["cpu"]["stats"]["speeds"] = [i for i in psutil.cpu_freq()]


    return info_dict

def ram_info():
    # RAM info
    info_dict = {}
    info_dict["ram"] = {}
    ram = psutil.virtual_memory()
    info_dict["ram"]["total"] = round(ram.total / 1000000000, ndigits=2)
    info_dict["ram"]["available"] = round(ram.available / 1000000000, ndigits=3)
    info_dict["ram"]["used"] = round(ram.used / 1000000000, ndigits=3)
    info_dict["ram"]["percentage_used"] = ram.percent

    return info_dict

def disks_info():
    # Disks info
    info_dict = {}
    info_dict["disks"] = {}
    # base for disks
    disks = psutil.disk_partitions()
    info_dict["disks"]["names"] = [i.device for i in disks]
    info_dict["disks"]["mount_points"] = [i.mountpoint for i in disks]
    info_dict["disks"]["options"] = [i.opts for i in disks]
    # usage
    base_disk_info = [psutil.disk_usage(i) for i in info_dict["disks"]["names"]]
    info_dict["disks"]["usage"] = {}
    info_dict["disks"]["usage"]["total_gb"] = [i.total/1024/1024/1024 for i in base_disk_info]
    info_dict["disks"]["usage"]["available_gb"] = [i.free/1024/1024/1024 for i in base_disk_info]
    info_dict["disks"]["usage"]["used_gb"] = [i.used/1024/1024/1024 for i in base_disk_info]
    info_dict["disks"]["usage"]["percentage_used"] = [i.percent for i in base_disk_info]

    return info_dict

# runs a scrape to a site that returns your isp and other very personal info
def get_isp():
    try:
        isp_info = req.get("https://ipinfo.io").content.decode()
        isp_info_g['net_info'] = isp_info
    except ConnectionError:
        po("connection could not be made, exiting")
        quit()

isp_info_g = {'net_info': {}}

def net_info():
    # Internet info
    info_dict = {}
    info_dict["net"] = {}
    # base for net
    network = psutil.net_io_counters()
    # for bytes
    info_dict["net"]["bytes_info"] = {}
    info_dict["net"]["bytes_info"]["sent"] = network.bytes_sent/1024/1024/1024
    info_dict["net"]["bytes_info"]["recieved"] = network.bytes_recv/1024/1024/1024
    # for packets
    info_dict["net"]["packets_info"] = {}
    info_dict["net"]["packets_info"]["sent"] = network.packets_sent/1000000
    info_dict["net"]["packets_info"]["recieved"] = network.packets_recv/1000000
    # for errors and loss
    info_dict["net"]["errors"] = {}
    info_dict["net"]["loss"] = {}

    info_dict["net"]["errors"]["in"] = network.errin
    info_dict["net"]["errors"]["out"] = network.errout
    info_dict["net"]["loss"]["in"] = network.dropin
    info_dict["net"]["loss"]["out"] = network.dropout

    info_dict["net"]["net_info"] = isp_info_g["net_info"]

    return info_dict

def processes_info():
    # Processes info
    info_dict = {}
    info_dict["processes"] = {}
    # ids
    ids = psutil.process_iter(['pid', 'name', 'cmdline'])
    ids = [i.info for i in ids]
    info_dict["processes"]["ids"] = [i['pid'] for i in ids]
    info_dict["processes"]["names"] = [i['name'] for i in ids]
    info_dict["processes"]["command"] = []
    for i in ids:
        if i["cmdline"] != None:
            info_dict["processes"]["command"].append(" ".join(x for x in i["cmdline"]))
        else:
            info_dict["processes"]["command"].append("_")
    
    return info_dict


def base(information_dictionary:dict,
         net_buff_info:list,
         disk_info:list,
         memory_ram_info:list,
         cpu_buff_info:list,
         isp_info_d:dict,
         textual_cpu_info:list,
         textual_proc_info:list,
         textual_mem_info:list,
         total_ram:float):
    global net_p_in_max

    lay = Layout()
    # split into two: the accessories a.k.a the headings, pics and creds area and the main area i.e are that will show main info
    lay.split_column(
        Layout(Panel("acessories-display"), name="acessories-display"),
        Layout(Panel("main-display"), name="main-display")
    )
    # set size
    lay["acessories-display"].size = 24

    # split again for a heading space and a space for the pic
    lay["acessories-display"].split_row(
        # curr font = big_money-se
        Layout(name="heading-space"),
        Layout(
            Align.center(arts.art_8, vertical="middle"), name="pic")
    )
    lay["acessories-display"]["pic"].size = 70

    # split heading space since its too large just for heading so some basic pc info can be shown there
    lay["acessories-display"]["heading-space"].split_column(
        Layout(name="heading"),
        Layout(name="pc-basic-info")
    )

    # set size to just fit the heading
    lay["acessories-display"]["heading"].size = 10

    # split it again for a credits section and to size the heading space to be just perfect
    # credits tree
    credits_info = Tree("[bold white on blue]\nCreated by:[/bold white on blue] Muaaz Khan\n\n[red on white]Socials[/red on white]")
    credits_info.add("[link=https://www.instagram.com/muaaz_ur_habibi?igsh=YzU3YnlxbzN5ZG9k]Instagram")
    credits_info.add("[link=https://github.com/thegigacoder123]Github")

    lay["acessories-display"]["heading"].split_row(
        Layout(Panel(figlet_format("Ter ma tus",
                             font="colossal",
                             width=110),
                             style="white on black", border_style="black"), name="actual-heading"),
        Layout(
            renderable=Panel(credits_info,
                                border_style="blue bold",
                                box=box.SQUARE,
                                title="[royal_blue1]|Creator Info|",
                                title_align="left"),
                                name="credits")
    )

    lay['acessories-display']['heading']['actual-heading'].size = 80
    #-------------------------------------ALL THIS WAS FOR THE HEADING SPACE--------------------------------------

    #----------NOW START ADDING THE MAIN INFO------------------
    # adding basic pc info
    basic_pc_info = f"""
[bold dark_green]Architecture[/bold dark_green]: {information_dictionary['arch']}
[bold dark_green]Network Name[/bold dark_green]: {information_dictionary['net_name']}
[bold dark_green]Operating System[/bold dark_green]: {information_dictionary['os']}
[bold dark_green]System[/bold dark_green]: {information_dictionary['system']}
[bold dark_green]Boot Time[/bold dark_green]: {information_dictionary['boot_time']}
[bold dark_green]Users[/bold dark_green]: {information_dictionary['users']}"""

    lay['acessories-display']['heading-space']['pc-basic-info'].update(Panel(basic_pc_info,
                                                                             box=box.SQUARE,
                                                                             border_style="light_green",
                                                                             title="[red]|Basic PC Information|",
                                                                             title_align="left"))
    # splitting main display section to 3 parts: CPU, Network and Memory
    lay['main-display'].split_row(
        Layout(name="cpu-display"),
        Layout(name="net-display"),
        Layout(name="mem-display")
    )


    # adding network info
    # dividiing net-display into two secs: graphs and texts
    lay['main-display']['net-display'].split_column(
        Layout(name="textual-data"),
        Layout(name="graphical-data")
    )

    # ignore this. it just cleans the net info
    backslash_replace = "\n  "
    quote_replace = '"'
    cleaned_net_info = str(isp_info_d['net_info']).replace('{', '').replace('}', '').replace(backslash_replace, '').replace(quote_replace, '').split(',')

    # displaying the texts
    lay["main-display"]["net-display"]["textual-data"].update(
        Panel(
            border_style="deep_pink3",
            box=box.SQUARE,
            title="[orange bold]|Internet|", title_align="left",
            renderable=Group(
                #f"[bold underline]General Info:[/bold underline]",
                Panel(
                    f"\n{cleaned_net_info[0]}\narea: {cleaned_net_info[1].split(': ')[1]}, {cleaned_net_info[2].split(': ')[1]}, {cleaned_net_info[3].split(': ')[1]}\nISP: {cleaned_net_info[6].split(': ')[1]}",
                    border_style="black", title="[purple bold underline]General Info", title_align="left"),
                Panel(
                    f"Bytes Recieved:       {round(float(net_buff_info[0][-1]), ndigits=4)} (mb/s)\nPackets Recieved:     {round(float(net_buff_info[2][-1]), ndigits=3)} (Mib/s)\n\nBytes Sent:           {round(float(net_buff_info[1][-1]), ndigits=4)} (mb/s)\nPackets Sent:         {round(float(net_buff_info[3][-1]), ndigits=3)} (Mib/s)\n\nPacket loss (In):     {round(float(net_buff_info[4][-1]), ndigits=3)} (b)\nPacket loss (Out):    {round(float(net_buff_info[5][-1]), ndigits=3)} (b)",
                    border_style="black", title="[purple bold underline]Statistical Data", title_align="left"
                )
            )
        )
    )

    # displaying the graphs
    lay["main-display"]["net-display"]["graphical-data"].split_row(
        Layout(name="bytes-graph"),
        Layout(name="packets-graph")
    )

    lay["main-display"]["net-display"]["graphical-data"].size = 16

    lay["main-display"]["net-display"]["graphical-data"]["bytes-graph"].update(
        Group(
            Panel(
                acp.plot([round(i, ndigits=4) for i in net_buff_info[0]], {"min": 0, "height": 5, "max": [round(i, ndigits=4) for i in net_buff_info[0]][-1]+0.5}),
                title="Bytes(mb): In", title_align="left", style="blue on black", border_style="deep_pink3", box=box.SQUARE
            ),
            Panel(
                acp.plot([round(i, ndigits=4) for i in net_buff_info[1]], {"min": 0, "height": 5, "max": [round(i, ndigits=4) for i in net_buff_info[1]][-1]+0.5}),
                title="Bytes(mb): Out", title_align="left", style="red on black", border_style="deep_pink3", box=box.SQUARE
            )
        )
    )

    lay["main-display"]["net-display"]["graphical-data"]["packets-graph"].update(
        Group(
            Panel(
                acp.plot(net_buff_info[2], {"min": 0, "height": 5}),
                title="Packets: In", title_align="left", style="blue on black", border_style="deep_pink3", box=box.SQUARE
            ),
            Panel(
                acp.plot(net_buff_info[3], {"min": 0, "height": 5}),
                title="Packets: Out", title_align="left", style="red on black", border_style="deep_pink3", box=box.SQUARE
            )
        )
    )


    # adding memory/ram info
    # cutting the display into two areas: graphs and text
    lay["main-display"]["mem-display"].split_column(
        Layout(name="textual-data"),
        Layout(name="graphical-data")
    )

    lay["main-display"]["mem-display"]["graphical-data"].size = 16
    # displaying the texts

    # the table that holds all the info regarding the storage space in the disks
    disks_usage_info_table = Table(border_style="navy_blue", box=box.MINIMAL)
    disks_usage_info_table.add_column("[blue1]Name")
    disks_usage_info_table.add_column("[blue1]Available")
    disks_usage_info_table.add_column("[blue1]Used")
    disks_usage_info_table.add_column("[blue1]Percent")

    for i in range(len(textual_mem_info[0])):
        disks_usage_info_table.add_row(f"{textual_mem_info[0][i]}", f"{str(round(float(textual_mem_info[4][i]), ndigits=2)) if textual_mem_info[4][i] != '' else ''} gb", f"{str(round(float(textual_mem_info[5][i]), ndigits=2)) if textual_mem_info[5][i] != '' else ''} gb", f"{textual_mem_info[6][i]}")

    lay["main-display"]["mem-display"]["textual-data"].update(
        Panel(
            Group(
                Panel(
                    'Names\n'+'\n'.join(i for i in textual_mem_info[0]) + '\n\n'+'Mount Points\n'+'\n'.join(i for i in textual_mem_info[1]),
                    title="[blue1 underline]Disks", title_align="left", border_style="black"
                ),
                disks_usage_info_table
            ), title="[cyan]|Memory|", title_align="left", border_style="navy_blue"
        )
    )

    # displaying the graphs
    lay["main-display"]["mem-display"]["graphical-data"].update(
        Group(
            Panel(
                acp.plot(memory_ram_info[0], {"min": 0, "height": 5, "max": total_ram}),
                title="[cyan]RAM: Available(gb)", title_align="left", border_style="navy_blue", box=box.SQUARE
            ),
            Panel(
                acp.plot(memory_ram_info[1], {"min": 0, "height": 5, "max": memory_ram_info[1][-1]+0.4}),
                title="[cyan]RAM: Used(gb)", title_align="left", border_style="navy_blue", box=box.SQUARE
            )
        )
    )


    # adding cpu info
    # cutting layout to two: graphical and textual

    lay["main-display"]["cpu-display"].split_column(
        Layout(name="textual-data"),
        Layout(name="graphical-data"),
        Layout(name="running-processes")
    )

    indivisual_cpu_info_table = Table(width=69, box=None)
    indivisual_cpu_info_table.add_column("[yellow]CPU")
    indivisual_cpu_info_table.add_column("[yellow]Time")
    indivisual_cpu_info_table.add_column("[yellow]Speed")

    for i in range(int(textual_cpu_info[2])):
        # support for windows since psutil doesnt have indivisual cpu speeds on windows
        indivisual_cpu_info_table.add_row(str(i+1), str(round(textual_cpu_info[3][i], ndigits=2)), str(textual_cpu_info[4][0]) if len(textual_cpu_info[4])!=0 else str(textual_cpu_info[4][i]))

    lay["main-display"]["cpu-display"]["textual-data"].update(
        Group(
            Panel(
                f'{textual_cpu_info[0]}\nArchitecture: {textual_cpu_info[1]}\nCores: {textual_cpu_info[2]}',
                border_style="dark_orange", title="[orange_red1]|CPU|", title_align="left", style="yellow", box=box.SQUARE
            ),
            indivisual_cpu_info_table
        )
    )

    lay["main-display"]["cpu-display"]["graphical-data"].size = 13

    lay["main-display"]["cpu-display"]["graphical-data"].update(
        Panel(
            acp.plot(cpu_buff_info, {"min": 0, "height": 10, "max": 100}),
            border_style="dark_orange", style="yellow", title="[orange_red1]CPU Utilisation (%)", title_align="left", box=box.SQUARE
        )
    )

    processes_info_table = Table(box=box.MINIMAL)
    processes_info_table.add_column("[plum2]I.D", overflow="crop")
    processes_info_table.add_column("[plum2]Name", overflow="crop")
    processes_info_table.add_column("[plum2]Command", overflow="crop")

    for i in range(len(textual_proc_info[0])):
        processes_info_table.add_row(f"[hot_pink3]{str(textual_proc_info[0][i])}", f"[hot_pink3]{str(textual_proc_info[1][i])}", f"[hot_pink3]{str(textual_proc_info[2][i])}")

    lay["main-display"]["cpu-display"]["running-processes"].update(
        processes_info_table
    )


    return lay


get_isp()
with Live(renderable=base(information_dictionary=basic_info(),
                          net_buff_info=[[0], [0], [0], [0], [0], [0]],
                          disk_info=[[0], [0], [0], [0]],
                          memory_ram_info=[[0], [0], [0], [0]],
                          cpu_buff_info=[0],
                          isp_info_d=isp_info_g,
                          textual_cpu_info=["", "", 0, [], []],
                          textual_proc_info=[[], [], []],
                          textual_mem_info=[[""], [""], [""], [""], [""], [""], [""]],
                          total_ram=float(0.0)),
                          refresh_per_second=100,
                          screen=False) as l:
    try:
        
        # buffers for the graph data, to help graph be a series and not a point
        net_b_in_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        net_b_out_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        net_p_in_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        net_p_out_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        net_e_in_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        net_e_out_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        net_p_in_loss_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        net_p_out_loss_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        ram_totl_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ram_avai_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ram_used_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ram_perc_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        total_ram = ram_info()["ram"]['total']

        disk_totl_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        disk_avai_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        disk_used_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        disk_perc_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        cpu_perc_buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        while True:

            net_b_in_buffer.append(net_info()["net"]["bytes_info"]["recieved"])
            net_b_out_buffer.append(net_info()["net"]["bytes_info"]["sent"])
            net_p_in_buffer.append(net_info()["net"]["packets_info"]["recieved"])
            net_p_out_buffer.append(net_info()["net"]["packets_info"]["sent"])
            net_e_in_buffer.append(net_info()["net"]["errors"]["in"])
            net_e_out_buffer.append(net_info()["net"]["errors"]["out"])
            net_p_in_loss_buffer.append(net_info()["net"]["loss"]["in"])
            net_p_out_loss_buffer.append(net_info()["net"]["loss"]["out"])

            ram_totl_buffer.append(ram_info()["ram"]["total"])
            ram_avai_buffer.append(ram_info()["ram"]["available"])
            ram_used_buffer.append(ram_info()["ram"]["used"])
            ram_perc_buffer.append(ram_info()["ram"]["percentage_used"])

            #disk_totl_buffer.append(disks_info()["disks"]["usage"]["total_gb"])
            #disk_avai_buffer.append(disks_info()["disks"]["usage"]["available_gb"])
            #disk_used_buffer.append(disks_info()["disks"]["usage"]["used_gb"])
            #disk_perc_buffer.append(disks_info()["disks"]["usage"]["percentage_used"])

            _cpu_info = cpu_info()

            cpu_perc_buffer.append(_cpu_info["cpu"]["stats"]["percent_used"])
            textual_cpu_data = [_cpu_info["cpu"]["name"], _cpu_info["cpu"]["arch"], _cpu_info["cpu"]["stats"]["cores"], _cpu_info["cpu"]["stats"]["times"], _cpu_info["cpu"]["stats"]["speeds"]]
            
            _processes_info = processes_info()
            textual_proc_data = [_processes_info["processes"]["ids"], _processes_info["processes"]["names"], _processes_info["processes"]["command"]]

            _ram_info = ram_info()
            _dsk_info = disks_info()

            textual_mem_data = [_dsk_info["disks"]["names"], _dsk_info["disks"]["mount_points"], _dsk_info["disks"]["options"], _dsk_info["disks"]["usage"]["total_gb"], _dsk_info["disks"]["usage"]["available_gb"], _dsk_info["disks"]["usage"]["used_gb"], _dsk_info["disks"]["usage"]["percentage_used"]]

            net_b_in_buffer = truncate_list(net_b_in_buffer, 20)
            net_b_out_buffer = truncate_list(net_b_out_buffer, 20)
            net_p_in_buffer = truncate_list(net_p_in_buffer, 20)
            net_p_out_buffer = truncate_list(net_p_out_buffer, 20)
            # length of these really dont matter, since they arent going 
            # to be displayed on graphs
            net_e_in_buffer = truncate_list(net_e_in_buffer, 20)
            net_e_out_buffer = truncate_list(net_e_out_buffer, 20)
            net_p_in_loss_buffer = truncate_list(net_p_in_loss_buffer, 20)
            net_p_out_loss_buffer = truncate_list(net_p_out_loss_buffer, 20)


            ram_avai_buffer = truncate_list(ram_avai_buffer, 40)
            ram_perc_buffer = truncate_list(ram_perc_buffer, 20)
            ram_used_buffer = truncate_list(ram_used_buffer, 40)
            ram_totl_buffer = truncate_list(ram_totl_buffer, 20)

            #disk_avai_buffer = truncate_list(disk_avai_buffer, 20)
            #disk_perc_buffer = truncate_list(disk_perc_buffer, 20)
            #disk_totl_buffer = truncate_list(disk_totl_buffer, 20)
            #disk_used_buffer = truncate_list(disk_used_buffer, 20)

            cpu_perc_buffer = truncate_list(cpu_perc_buffer, 50)

            
            l.update(base(basic_info(),
                        net_buff_info=[net_b_in_buffer, net_b_out_buffer, net_p_in_buffer, net_p_out_buffer, net_e_in_buffer, net_e_out_buffer, net_p_in_loss_buffer, net_p_out_loss_buffer],
                        disk_info=[disk_avai_buffer, disk_used_buffer, disk_perc_buffer, disk_totl_buffer],
                        memory_ram_info=[ram_avai_buffer, ram_used_buffer, ram_perc_buffer, ram_totl_buffer],
                        cpu_buff_info=cpu_perc_buffer,
                        textual_cpu_info=textual_cpu_data,
                        textual_proc_info=textual_proc_data,
                        textual_mem_info=textual_mem_data,
                        isp_info_d=isp_info_g,
                        total_ram=float(total_ram)))
    except KeyboardInterrupt:
        quit()
