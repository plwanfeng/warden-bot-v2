import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import asyncio
import threading
import json
import os
from datetime import datetime
from warden import ProtocolTaskManager
from utils import print_timestamped_message, read_json_file_data, extract_wallet_address_info

class ProtocolManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Warden 小号保活自动化工具 by 晚风")
        self.root.geometry("1282x961")  # 宽度和高度都减少20% (1602*0.8=1282, 1201*0.8=961)
        self.root.configure(bg='#ffffff')
        self.root.minsize(1098, 841)  # 最小尺寸也相应调整 (1373*0.8=1098, 1051*0.8=841)
        
        # 任务管理器实例
        self.task_manager = ProtocolTaskManager()
        self.is_running = False
        self.current_thread = None
        
        # 样式配置
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        self.create_widgets()
        self.load_initial_data()
        
    def configure_styles(self):
        """配置GUI样式"""
        # 标题样式
        self.style.configure('Title.TLabel', 
                           font=('Microsoft YaHei', 18, 'bold'),
                           foreground='#000000',
                           background='#ffffff')
        
        # 子标题样式
        self.style.configure('Heading.TLabel',
                           font=('Microsoft YaHei', 12, 'bold'),
                           foreground='#000000',
                           background='#ffffff')
        
        # 信息标签样式
        self.style.configure('Info.TLabel',
                           font=('Microsoft YaHei', 10),
                           foreground='#333333',
                           background='#ffffff')
        
        # 成功状态样式
        self.style.configure('Success.TLabel',
                           font=('Microsoft YaHei', 10),
                           foreground='#008000',
                           background='#ffffff')
        
        # 错误状态样式
        self.style.configure('Error.TLabel',
                           font=('Microsoft YaHei', 10),
                           foreground='#cc0000',
                           background='#ffffff')
        
        # 普通按钮样式
        self.style.configure('Custom.TButton',
                           font=('Microsoft YaHei', 10),
                           padding=(10, 5),
                           background='#f0f0f0',
                           foreground='#000000')
        
        # 主要按钮样式
        self.style.configure('Primary.TButton',
                           font=('Microsoft YaHei', 11, 'bold'),
                           padding=(15, 8),
                           background='#e0e0e0',
                           foreground='#000000')
        
        # 框架样式
        self.style.configure('Card.TFrame',
                           background='#ffffff',
                           relief='solid',
                           borderwidth=1)
        
        # Treeview样式
        self.style.configure('Treeview',
                           background='#ffffff',
                           foreground='#000000',
                           fieldbackground='#ffffff',
                           font=('Microsoft YaHei', 9))
        
        self.style.configure('Treeview.Heading',
                           background='#f0f0f0',
                           foreground='#000000',
                           font=('Microsoft YaHei', 10, 'bold'))
        
    def create_widgets(self):
        """创建GUI组件"""
        # 主容器 - 直接开始，不需要标题
        main_frame = tk.Frame(self.root, bg='#ffffff')
        main_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        # 上半部分：左侧控制面板 + 右侧账户列表
        top_frame = tk.Frame(main_frame, bg='#ffffff')
        top_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # 左侧控制面板
        left_frame = tk.Frame(top_frame, bg='#ffffff', relief='solid', bd=1, width=280)
        left_frame.pack(side='left', fill='y', padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # 右侧账户列表面板
        account_list_frame = tk.Frame(top_frame, bg='#ffffff', relief='solid', bd=1)
        account_list_frame.pack(side='right', fill='both', expand=True)
        
        # 下半部分：日志面板
        bottom_frame = tk.Frame(main_frame, bg='#ffffff', relief='solid', bd=1, height=160)
        bottom_frame.pack(fill='x')
        bottom_frame.pack_propagate(False)
        
        self.create_control_panel(left_frame)
        self.create_account_list_panel(account_list_frame)
        self.create_log_panel(bottom_frame)
        
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = tk.Frame(parent, bg='#ffffff')
        control_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 账户管理部分
        account_frame = tk.LabelFrame(control_frame, text="📁 账户管理", 
                                     bg='#ffffff', fg='#000000', 
                                     font=('Microsoft YaHei', 10, 'bold'),
                                     relief='flat', bd=0,
                                     labelanchor='nw')
        account_frame.pack(fill='x', pady=(0, 10))
        
        # 账户文件选择 - 紧凑布局
        file_frame = tk.Frame(account_frame, bg='#ffffff')
        file_frame.pack(fill='x', padx=8, pady=8)
        
        ttk.Label(file_frame, text="文件:", style='Info.TLabel').pack(side='left')
        self.account_file_var = tk.StringVar(value="accounts_example.txt")
        ttk.Entry(file_frame, textvariable=self.account_file_var, 
                 width=15, font=('Microsoft YaHei', 9)).pack(side='left', padx=(5, 5))
        ttk.Button(file_frame, text="浏览", command=self.browse_account_file,
                  style='Custom.TButton').pack(side='left')
        
        # 账户数量显示
        self.account_count_var = tk.StringVar(value="账户数量: 0")
        ttk.Label(account_frame, textvariable=self.account_count_var,
                 style='Info.TLabel').pack(padx=8, pady=(0, 8))
        
        # 代理设置部分
        proxy_frame = tk.LabelFrame(control_frame, text="🌐 代理设置", 
                                   bg='#ffffff', fg='#000000',
                                   font=('Microsoft YaHei', 10, 'bold'),
                                   relief='flat', bd=0,
                                   labelanchor='nw')
        proxy_frame.pack(fill='x', pady=(0, 10))
        
        # 代理模式选择 - 紧凑布局
        self.proxy_mode_var = tk.StringVar(value="no_proxy")
        radio_frame = tk.Frame(proxy_frame, bg='#ffffff')
        radio_frame.pack(fill='x', padx=8, pady=5)
        
        tk.Radiobutton(radio_frame, text="不使用代理", variable=self.proxy_mode_var,
                      value="no_proxy", bg='#ffffff', fg='#000000',
                      selectcolor='#ffffff', activebackground='#ffffff',
                      activeforeground='#000000', font=('Microsoft YaHei', 9)).pack(side='left')
        tk.Radiobutton(radio_frame, text="使用私人代理", variable=self.proxy_mode_var,
                      value="private_proxy", bg='#ffffff', fg='#000000',
                      selectcolor='#ffffff', activebackground='#ffffff',
                      activeforeground='#000000', font=('Microsoft YaHei', 9)).pack(side='left', padx=(20, 0))
        
        # 代理文件选择 - 紧凑布局
        proxy_file_frame = tk.Frame(proxy_frame, bg='#ffffff')
        proxy_file_frame.pack(fill='x', padx=8, pady=5)
        
        ttk.Label(proxy_file_frame, text="文件:", style='Info.TLabel').pack(side='left')
        self.proxy_file_var = tk.StringVar(value="proxy.txt")
        ttk.Entry(proxy_file_frame, textvariable=self.proxy_file_var,
                 width=15, font=('Microsoft YaHei', 9)).pack(side='left', padx=(5, 5))
        ttk.Button(proxy_file_frame, text="浏览", command=self.browse_proxy_file,
                  style='Custom.TButton').pack(side='left')
        
        # 代理轮换选项和数量 - 并排显示
        bottom_frame = tk.Frame(proxy_frame, bg='#ffffff')
        bottom_frame.pack(fill='x', padx=8, pady=5)
        
        self.rotate_proxy_var = tk.BooleanVar()
        tk.Checkbutton(bottom_frame, text="轮换无效代理", variable=self.rotate_proxy_var,
                      bg='#ffffff', fg='#000000', selectcolor='#ffffff',
                      activebackground='#ffffff', activeforeground='#000000',
                      font=('Microsoft YaHei', 9)).pack(side='left')
        
        self.proxy_count_var = tk.StringVar(value="代理数量: 0")
        ttk.Label(bottom_frame, textvariable=self.proxy_count_var,
                 style='Info.TLabel').pack(side='right')
        
        # 任务设置部分
        task_frame = tk.LabelFrame(control_frame, text="⚙️ 任务设置", 
                                  bg='#ffffff', fg='#000000',
                                  font=('Microsoft YaHei', 10, 'bold'),
                                  relief='flat', bd=0,
                                  labelanchor='nw')
        task_frame.pack(fill='x', pady=(0, 10))
        
        # 任务选项 - 紧凑布局
        task_options_frame = tk.Frame(task_frame, bg='#ffffff')
        task_options_frame.pack(fill='x', padx=8, pady=5)
        
        self.checkin_var = tk.BooleanVar(value=True)
        tk.Checkbutton(task_options_frame, text="每日签到", variable=self.checkin_var,
                      bg='#ffffff', fg='#000000', selectcolor='#ffffff',
                      activebackground='#ffffff', activeforeground='#000000',
                      font=('Microsoft YaHei', 9)).pack(side='left')
        
        self.game_var = tk.BooleanVar(value=True)
        tk.Checkbutton(task_options_frame, text="游戏活动", variable=self.game_var,
                      bg='#ffffff', fg='#000000', selectcolor='#ffffff',
                      activebackground='#ffffff', activeforeground='#000000',
                      font=('Microsoft YaHei', 9)).pack(side='left', padx=(10, 0))
        
        self.chat_var = tk.BooleanVar(value=True)
        tk.Checkbutton(task_options_frame, text="AI聊天", variable=self.chat_var,
                      bg='#ffffff', fg='#000000', selectcolor='#ffffff',
                      activebackground='#ffffff', activeforeground='#000000',
                      font=('Microsoft YaHei', 9)).pack(side='left', padx=(10, 0))
        
        # 循环设置 - 紧凑布局
        cycle_frame = tk.Frame(task_frame, bg='#ffffff')
        cycle_frame.pack(fill='x', padx=8, pady=5)
        
        ttk.Label(cycle_frame, text="循环间隔(小时):", style='Info.TLabel').pack(side='left')
        self.cycle_interval_var = tk.StringVar(value="24")
        ttk.Entry(cycle_frame, textvariable=self.cycle_interval_var,
                 width=8, font=('Microsoft YaHei', 9)).pack(side='left', padx=(5, 0))
        
        # 状态显示部分
        status_frame = tk.LabelFrame(control_frame, text="📊 运行状态", 
                                    bg='#ffffff', fg='#000000',
                                    font=('Microsoft YaHei', 10, 'bold'),
                                    relief='flat', bd=0,
                                    labelanchor='nw')
        status_frame.pack(fill='x', pady=(0, 10))
        
        status_info_frame = tk.Frame(status_frame, bg='#ffffff')
        status_info_frame.pack(fill='x', padx=8, pady=5)
        
        self.status_var = tk.StringVar(value="状态: 待机")
        ttk.Label(status_info_frame, textvariable=self.status_var,
                 style='Info.TLabel').pack(anchor='w')
        
        self.progress_var = tk.StringVar(value="进度: 0/0")
        ttk.Label(status_info_frame, textvariable=self.progress_var,
                 style='Info.TLabel').pack(anchor='w', pady=(2, 0))
        
        # 控制按钮 - 紧凑布局
        button_frame = tk.Frame(control_frame, bg='#ffffff')
        button_frame.pack(fill='x', pady=10)
        
        self.start_button = ttk.Button(button_frame, text="▶️ 开始运行",
                                      command=self.start_bot,
                                      style='Primary.TButton')
        self.start_button.pack(fill='x', pady=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ 停止运行",
                                     command=self.stop_bot,
                                     style='Primary.TButton',
                                     state='disabled')
        self.stop_button.pack(fill='x', pady=(0, 5))
        
        ttk.Button(button_frame, text="🗑️ 清空日志",
                  command=self.clear_log,
                  style='Custom.TButton').pack(fill='x')
        
    def create_account_list_panel(self, parent):
        """创建账户列表面板"""
        account_frame = tk.Frame(parent, bg='#ffffff')
        account_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # 账户列表标题
        title_frame = tk.Frame(account_frame, bg='#ffffff')
        title_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(title_frame, text="📋 账户列表", style='Heading.TLabel').pack(side='left')
        
        # 刷新按钮
        ttk.Button(title_frame, text="🔄 刷新列表", command=self.refresh_account_list,
                  style='Custom.TButton').pack(side='right')
        
        # 账户列表容器
        list_container = tk.Frame(account_frame, bg='#ffffff')
        list_container.pack(fill='both', expand=True)
        
        # 创建Treeview来显示账户列表
        columns = ('序号', '地址', '签到', '游戏', '聊天', '积分', '最后活动')
        self.account_tree = ttk.Treeview(list_container, columns=columns, show='headings')
        
        # 设置列标题
        self.account_tree.heading('序号', text='序号')
        self.account_tree.heading('地址', text='钱包地址')
        self.account_tree.heading('签到', text='每日签到')
        self.account_tree.heading('游戏', text='游戏活动')
        self.account_tree.heading('聊天', text='AI聊天')
        self.account_tree.heading('积分', text='积分')
        self.account_tree.heading('最后活动', text='最后活动时间')
        
        # 设置列宽
        self.account_tree.column('序号', width=60, anchor='center')
        self.account_tree.column('地址', width=200, anchor='center')
        self.account_tree.column('签到', width=100, anchor='center')
        self.account_tree.column('游戏', width=100, anchor='center')
        self.account_tree.column('聊天', width=100, anchor='center')
        self.account_tree.column('积分', width=120, anchor='center')
        self.account_tree.column('最后活动', width=140, anchor='center')
        
        # 只添加垂直滚动条
        scrollbar_y = ttk.Scrollbar(list_container, orient='vertical', command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=scrollbar_y.set)
        
        # 布局 - 修复滚动条位置
        self.account_tree.pack(side='left', fill='both', expand=True)
        scrollbar_y.pack(side='right', fill='y')
        
        # 绑定右键菜单
        self.account_tree.bind("<Button-3>", self.show_context_menu)
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0, bg='#ffffff', fg='#000000')
        self.context_menu.add_command(label="▶️ 运行选中账户", command=self.run_selected_account)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="ℹ️ 查看详细信息", command=self.show_account_details)
        
        # 账户统计信息
        stats_frame = tk.Frame(account_frame, bg='#ffffff')
        stats_frame.pack(fill='x', pady=(15, 0))
        
        # 分隔线
        separator = tk.Frame(stats_frame, bg='#e0e0e0', height=1)
        separator.pack(fill='x', pady=(0, 10))
        
        stats_info_frame = tk.Frame(stats_frame, bg='#ffffff')
        stats_info_frame.pack(fill='x')
        
        self.total_accounts_var = tk.StringVar(value="总账户: 0")
        self.active_accounts_var = tk.StringVar(value="活跃账户: 0")
        self.total_balance_var = tk.StringVar(value="总积分: 0")
        
        ttk.Label(stats_info_frame, textvariable=self.total_accounts_var, style='Info.TLabel').pack(side='left', padx=(0, 20))
        ttk.Label(stats_info_frame, textvariable=self.active_accounts_var, style='Info.TLabel').pack(side='left', padx=(0, 20))
        ttk.Label(stats_info_frame, textvariable=self.total_balance_var, style='Info.TLabel').pack(side='left')
        
        # 初始化账户数据
        self.account_data = {}
        
    def create_log_panel(self, parent):
        """创建日志面板"""
        log_frame = tk.Frame(parent, bg='#ffffff')
        log_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # 日志标题
        title_frame = tk.Frame(log_frame, bg='#ffffff')
        title_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(title_frame, text="📝 运行日志", style='Heading.TLabel').pack(side='left')
        
        # 日志文本区域
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 bg='#ffffff', 
                                                 fg='#000000',
                                                 font=('Consolas', 9),
                                                 wrap=tk.WORD,
                                                 relief='flat',
                                                 bd=1,
                                                 insertbackground='#000000')
        self.log_text.pack(fill='both', expand=True)
        
        # 配置日志文本颜色标签
        self.log_text.tag_configure('info', foreground='#000000')
        self.log_text.tag_configure('success', foreground='#008000')
        self.log_text.tag_configure('warning', foreground='#cc6600')
        self.log_text.tag_configure('error', foreground='#cc0000')
        self.log_text.tag_configure('blue', foreground='#0066cc')
        self.log_text.tag_configure('cyan', foreground='#006666')
        self.log_text.tag_configure('magenta', foreground='#cc00cc')
        
    def browse_account_file(self):
        """浏览账户文件"""
        filename = filedialog.askopenfilename(
            title="选择账户文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.account_file_var.set(filename)
            self.load_account_count()
            self.refresh_account_list()
            
    def browse_proxy_file(self):
        """浏览代理文件"""
        filename = filedialog.askopenfilename(
            title="选择代理文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.proxy_file_var.set(filename)
            self.load_proxy_count()
            
    def load_initial_data(self):
        """加载初始数据"""
        self.load_account_count()
        self.load_proxy_count()
        self.refresh_account_list()
        
    def load_account_count(self):
        """加载账户数量"""
        try:
            filename = self.account_file_var.get()
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    accounts = [line.strip() for line in f if line.strip()]
                self.account_count_var.set(f"账户数量: {len(accounts)}")
            else:
                self.account_count_var.set("账户数量: 文件不存在")
        except Exception as e:
            self.account_count_var.set(f"账户数量: 读取错误")
            
    def load_proxy_count(self):
        """加载代理数量"""
        try:
            filename = self.proxy_file_var.get()
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    proxies = [line.strip() for line in f if line.strip()]
                self.proxy_count_var.set(f"代理数量: {len(proxies)}")
            else:
                self.proxy_count_var.set("代理数量: 文件不存在")
        except Exception as e:
            self.proxy_count_var.set(f"代理数量: 读取错误")
            
    def refresh_account_list(self):
        """刷新账户列表"""
        try:
            # 清空现有列表
            for item in self.account_tree.get_children():
                self.account_tree.delete(item)
            
            # 重新加载账户
            account_file = self.account_file_var.get()
            if os.path.exists(account_file):
                with open(account_file, 'r') as f:
                    account_keys = [line.strip() for line in f if line.strip()]
                
                total_balance = 0
                active_count = 0
                
                for i, key_entry in enumerate(account_keys):
                    wallet_address, masked_address = extract_wallet_address_info(key_entry)
                    
                    if wallet_address:
                        # 获取账户信息
                        account_info = self.account_data.get(wallet_address, {})
                        checkin_status = account_info.get('checkin_status', '未知')
                        game_status = account_info.get('game_status', '未知')
                        chat_status = account_info.get('chat_status', '未知')
                        balance = account_info.get('balance', 0)
                        last_activity = account_info.get('last_activity', '从未')
                        
                        # 统计活跃账户（所有任务都完成的账户）
                        completed_tasks = [checkin_status, game_status, chat_status]
                        if all(status in ['成功', '今日已完成'] for status in completed_tasks):
                            active_count += 1
                        
                        total_balance += balance
                        
                        # 添加到列表
                        self.account_tree.insert('', 'end', values=(
                            i + 1,
                            masked_address,
                            checkin_status,
                            game_status,
                            chat_status,
                            f"{balance:,}",
                            last_activity
                        ))
                    else:
                        self.account_tree.insert('', 'end', values=(
                            i + 1,
                            "无效私钥",
                            "错误",
                            "错误",
                            "错误",
                            "0",
                            "从未"
                        ))
                
                # 更新统计信息
                self.total_accounts_var.set(f"总账户: {len(account_keys)}")
                self.active_accounts_var.set(f"活跃账户: {active_count}")
                self.total_balance_var.set(f"总积分: {total_balance:,}")
                
            else:
                self.total_accounts_var.set("总账户: 文件不存在")
                self.active_accounts_var.set("活跃账户: 0")
                self.total_balance_var.set("总积分: 0")
                
        except Exception as e:
            self.log_to_gui(f"刷新账户列表出错: {str(e)}", 'error')
            
    def update_account_status(self, wallet_address, status=None, balance=None, last_activity=None, 
                             checkin_status=None, game_status=None, chat_status=None):
        """更新账户状态"""
        if wallet_address not in self.account_data:
            self.account_data[wallet_address] = {
                'checkin_status': '未知',
                'game_status': '未知', 
                'chat_status': '未知',
                'balance': 0,
                'last_activity': '从未'
            }
        
        if status is not None:
            self.account_data[wallet_address]['status'] = status
        if balance is not None:
            self.account_data[wallet_address]['balance'] = balance
        if last_activity is not None:
            self.account_data[wallet_address]['last_activity'] = last_activity
        if checkin_status is not None:
            self.account_data[wallet_address]['checkin_status'] = checkin_status
        if game_status is not None:
            self.account_data[wallet_address]['game_status'] = game_status
        if chat_status is not None:
            self.account_data[wallet_address]['chat_status'] = chat_status
        
        # 刷新显示
        self.refresh_account_list()
            
    def log_to_gui(self, message, tag='info'):
        """将消息记录到GUI日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message, tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        
    def start_bot(self):
        """开始运行机器人"""
        if self.is_running:
            return
            
        # 验证输入
        if not self.validate_inputs():
            return
            
        self.is_running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_var.set("状态: 运行中")
        
        # 在新线程中运行机器人
        self.current_thread = threading.Thread(target=self.run_bot_thread)
        self.current_thread.daemon = True
        self.current_thread.start()
        
    def stop_bot(self):
        """停止运行机器人"""
        self.is_running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_var.set("状态: 停止中...")
        self.log_to_gui("正在停止机器人...", 'warning')
        
    def validate_inputs(self):
        """验证输入参数"""
        # 检查账户文件
        account_file = self.account_file_var.get()
        if not os.path.exists(account_file):
            messagebox.showerror("错误", f"账户文件不存在: {account_file}")
            return False
            
        # 检查代理文件（如果使用代理）
        if self.proxy_mode_var.get() == "private_proxy":
            proxy_file = self.proxy_file_var.get()
            if not os.path.exists(proxy_file):
                messagebox.showerror("错误", f"代理文件不存在: {proxy_file}")
                return False
                
        # 检查循环间隔
        try:
            interval = float(self.cycle_interval_var.get())
            if interval <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("错误", "循环间隔必须是正数")
            return False
            
        return True
        
    def run_bot_thread(self):
        """在线程中运行机器人"""
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行机器人
            loop.run_until_complete(self.run_bot_async())
            
        except Exception as e:
            self.log_to_gui(f"运行错误: {str(e)}", 'error')
        finally:
            self.is_running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.status_var.set("状态: 已停止")
            
    async def run_bot_async(self):
        """异步运行机器人"""
        try:
            # 加载账户
            account_file = self.account_file_var.get()
            with open(account_file, 'r') as f:
                account_keys = [line.strip() for line in f if line.strip()]
                
            if not account_keys:
                self.log_to_gui("没有找到有效的账户", 'error')
                return
                
            # 加载问题列表
            chat_questions = read_json_file_data("question_lists.json")
            if not chat_questions:
                self.log_to_gui("无法加载问题列表", 'error')
                return
                
            # 设置代理
            use_proxy = self.proxy_mode_var.get() == "private_proxy"
            rotate_proxy = self.rotate_proxy_var.get()
            
            if use_proxy:
                await self.task_manager.initialize_proxy_config(True)
                if not self.task_manager.proxy_collection:
                    self.log_to_gui("警告: 未找到代理，将不使用代理运行", 'warning')
                    use_proxy = False
                    
            # 获取循环间隔
            cycle_hours = float(self.cycle_interval_var.get())
            cycle_seconds = int(cycle_hours * 3600)
            
            self.log_to_gui("🚀 开始运行Warden Protocol自动化机器人", 'success')
            self.log_to_gui(f"📊 总账户数: {len(account_keys)}", 'info')
            self.log_to_gui(f"🔄 循环间隔: {cycle_hours}小时", 'info')
            self.log_to_gui(f"🌐 代理状态: {'启用' if use_proxy else '禁用'}", 'info')
            
            while self.is_running:
                # 处理所有账户
                for i, key_entry in enumerate(account_keys):
                    if not self.is_running:
                        break
                        
                    wallet_address, masked_address = extract_wallet_address_info(key_entry)
                    
                    if not wallet_address:
                        self.log_to_gui(f"❌ 无效的私钥: {masked_address}", 'error')
                        continue
                        
                    self.progress_var.set(f"进度: {i+1}/{len(account_keys)}")
                    self.log_to_gui(f"🔄 处理账户: {masked_address}", 'blue')
                    
                    # 设置请求头
                    self.setup_headers(wallet_address)
                    
                    # 处理账户活动
                    await self.process_account_activities(key_entry, wallet_address, 
                                                        chat_questions, use_proxy, rotate_proxy)
                    
                    self.log_to_gui(f"✅ 账户处理完成: {masked_address}", 'success')
                    
                    if self.is_running:
                        await asyncio.sleep(5)
                        
                if not self.is_running:
                    break
                    
                # 等待下一个循环
                self.log_to_gui(f"⏰ 所有账户处理完成，等待{cycle_hours}小时后开始下一轮", 'cyan')
                self.progress_var.set("进度: 等待中...")
                
                for remaining in range(cycle_seconds, 0, -1):
                    if not self.is_running:
                        break
                        
                    hours = remaining // 3600
                    minutes = (remaining % 3600) // 60
                    seconds = remaining % 60
                    
                    self.status_var.set(f"状态: 等待中 ({hours:02d}:{minutes:02d}:{seconds:02d})")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.log_to_gui(f"运行异常: {str(e)}", 'error')
            
    def setup_headers(self, wallet_address):
        """设置请求头"""
        from utils import generate_random_browser_agent
        import uuid
        
        random_user_agent = generate_random_browser_agent()
        
        self.task_manager.auth_header_storage[wallet_address] = {
            "Accept": "application/json",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://app.wardenprotocol.org",
            "Privy-App-Id": "cm7f00k5c02tibel0m4o9tdy1",
            "Privy-Ca-Id": str(uuid.uuid4()),
            "Privy-Client": "react-auth:2.13.8",
            "Referer": "https://app.wardenprotocol.org/", 
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Storage-Access": "active",
            "User-Agent": random_user_agent
        }
        
        self.task_manager.api_header_storage[wallet_address] = {
            "Accept": "*/*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://app.wardenprotocol.org",
            "Referer": "https://app.wardenprotocol.org/", 
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": random_user_agent
        }
        
        self.task_manager.chat_header_storage[wallet_address] = {
            "Accept": "*/*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://app.wardenprotocol.org",
            "Referer": "https://app.wardenprotocol.org/", 
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": random_user_agent,
            "X-Api-Key": "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"
        }
        
    async def process_account_activities(self, private_key, wallet_address, chat_questions, use_proxy, rotate_proxy):
        """处理账户活动"""
        try:
            # 更新状态为处理中
            self.update_account_status(wallet_address, last_activity=datetime.now().strftime('%H:%M:%S'))
            
            # 显示代理使用情况
            if use_proxy and self.task_manager.proxy_collection:
                proxy = self.task_manager.fetch_assigned_proxy(wallet_address)
                self.log_to_gui(f"🔗 使用代理: {proxy}", 'info')
                
                # 测试代理连接
                self.log_to_gui("🔍 测试代理连接...", 'info')
                is_proxy_valid = await self.task_manager.test_network_connectivity(proxy)
                if is_proxy_valid:
                    self.log_to_gui("✅ 代理连接正常", 'success')
                else:
                    self.log_to_gui("❌ 代理连接失败", 'error')
                    if rotate_proxy:
                        self.log_to_gui("🔄 尝试切换代理...", 'info')
                        proxy = self.task_manager.switch_proxy_for_wallet(wallet_address)
                        self.log_to_gui(f"🔗 切换到代理: {proxy}", 'info')
                        is_proxy_valid = await self.task_manager.test_network_connectivity(proxy)
                        if is_proxy_valid:
                            self.log_to_gui("✅ 新代理连接正常", 'success')
                        else:
                            self.log_to_gui("❌ 新代理连接也失败", 'error')
            else:
                proxy = None
                self.log_to_gui("🌐 直接连接（无代理）", 'info')
            
            # 登录
            login_success = await self.task_manager.authenticate_wallet_session(private_key, wallet_address, use_proxy, rotate_proxy)
            if not login_success:
                self.log_to_gui("❌ 登录失败", 'error')
                self.update_account_status(wallet_address, 
                                         checkin_status='登录失败', 
                                         game_status='登录失败', 
                                         chat_status='登录失败',
                                         last_activity=datetime.now().strftime('%H:%M:%S'))
                return
                
            self.log_to_gui("✅ 登录成功", 'success')
            
            # 获取代理（如果之前没有获取）
            if proxy is None:
                proxy = self.task_manager.fetch_assigned_proxy(wallet_address) if use_proxy else None
            
            # 获取余额
            balance = 0
            user_data = await self.task_manager.retrieve_wallet_balance(wallet_address, proxy)
            if user_data:
                balance = user_data.get("token", {}).get("pointsTotal", 0)
                self.log_to_gui(f"💰 当前积分: {balance}", 'info')
                
            # 执行任务并记录每个任务的状态
            checkin_result = "未执行"
            game_result = "未执行"
            chat_result = "未执行"
            
            if self.checkin_var.get():
                checkin_result = await self.perform_checkin(wallet_address, proxy)
                    
            if self.game_var.get():
                game_result = await self.perform_game_activity(wallet_address, proxy)
                    
            if self.chat_var.get():
                chat_result = await self.perform_chat_activity(wallet_address, proxy, chat_questions)
            
            # 更新账户状态
            self.update_account_status(wallet_address, 
                                     balance=balance,
                                     checkin_status=checkin_result,
                                     game_status=game_result,
                                     chat_status=chat_result,
                                     last_activity=datetime.now().strftime('%H:%M:%S'))
                
        except Exception as e:
            self.log_to_gui(f"处理账户活动时出错: {str(e)}", 'error')
            self.update_account_status(wallet_address, 
                                     checkin_status='错误',
                                     game_status='错误',
                                     chat_status='错误',
                                     last_activity=datetime.now().strftime('%H:%M:%S'))
            
    async def perform_checkin(self, wallet_address, proxy):
        """执行签到"""
        try:
            result = await self.task_manager.process_daily_checkin(wallet_address, proxy)
            if result:
                if result.get("activityId"):
                    self.log_to_gui("✅ 每日签到: 成功", 'success')
                    return "成功"
                else:
                    message = result.get("message", "未知状态")
                    if "already recorded today" in message.lower() or "今日已完成" in message:
                        self.log_to_gui("✅ 每日签到: 今日已完成", 'success')
                        return "今日已完成"
                    else:
                        self.log_to_gui(f"⚠️ 每日签到: {message}", 'warning')
                        return "失败"
            else:
                self.log_to_gui("❌ 每日签到: 失败", 'error')
                return "失败"
        except Exception as e:
            error_msg = str(e)
            if "already recorded today" in error_msg.lower():
                self.log_to_gui("✅ 每日签到: 今日已完成", 'success')
                return "今日已完成"
            else:
                self.log_to_gui(f"签到出错: {error_msg}", 'error')
                return "失败"
            
    async def perform_game_activity(self, wallet_address, proxy):
        """执行游戏活动"""
        try:
            result = await self.task_manager.execute_game_task(wallet_address, proxy)
            if result:
                if result.get("activityId"):
                    self.log_to_gui("✅ 游戏活动: 成功", 'success')
                    return "成功"
                else:
                    message = result.get("message", "未知状态")
                    if "already recorded today" in message.lower() or "今日已完成" in message:
                        self.log_to_gui("✅ 游戏活动: 今日已完成", 'success')
                        return "今日已完成"
                    else:
                        self.log_to_gui(f"⚠️ 游戏活动: {message}", 'warning')
                        return "失败"
            else:
                self.log_to_gui("❌ 游戏活动: 失败", 'error')
                return "失败"
        except Exception as e:
            error_msg = str(e)
            if "already recorded today" in error_msg.lower():
                self.log_to_gui("✅ 游戏活动: 今日已完成", 'success')
                return "今日已完成"
            else:
                self.log_to_gui(f"游戏活动出错: {error_msg}", 'error')
                return "失败"
            
    async def perform_chat_activity(self, wallet_address, proxy, chat_questions):
        """执行聊天活动"""
        try:
            import random
            
            # 初始化聊天线程
            thread_info = await self.task_manager.initialize_agent_thread(wallet_address, proxy)
            if not thread_info:
                self.log_to_gui("❌ AI聊天: 初始化失败", 'error')
                return "失败"
                
            thread_id = thread_info.get("thread_id")
            question = random.choice(chat_questions)
            
            self.log_to_gui(f"💬 问题: {question}", 'cyan')
            
            # 执行聊天
            response = await self.task_manager.execute_agent_stream(wallet_address, thread_id, question, proxy)
            if response:
                # 限制显示长度
                display_response = response[:100] + "..." if len(response) > 100 else response
                self.log_to_gui(f"🤖 回答: {display_response}", 'magenta')
                
                # 提交聊天活动
                chat_result = await self.task_manager.submit_chat_activity(wallet_address, len(question), proxy)
                if chat_result and chat_result.get("activityId"):
                    self.log_to_gui("✅ AI聊天: 成功", 'success')
                    return "成功"
                else:
                    message = chat_result.get("message", "未知状态") if chat_result else "提交失败"
                    if "already recorded today" in message.lower() or "今日已完成" in message:
                        self.log_to_gui("✅ AI聊天: 今日已完成", 'success')
                        return "今日已完成"
                    else:
                        self.log_to_gui(f"⚠️ AI聊天: {message}", 'warning')
                        return "失败"
            else:
                self.log_to_gui("❌ AI聊天: 获取回答失败", 'error')
                return "失败"
                
        except Exception as e:
            error_msg = str(e)
            if "already recorded today" in error_msg.lower():
                self.log_to_gui("✅ AI聊天: 今日已完成", 'success')
                return "今日已完成"
            else:
                self.log_to_gui(f"AI聊天出错: {error_msg}", 'error')
            return "失败"
            
    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            # 选择点击的项目
            item = self.account_tree.identify_row(event.y)
            if item:
                self.account_tree.selection_set(item)
                self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.log_to_gui(f"显示右键菜单出错: {str(e)}", 'error')
            
    def run_selected_account(self):
        """运行选中的账户"""
        try:
            selected_items = self.account_tree.selection()
            if not selected_items:
                messagebox.showwarning("警告", "请先选择一个账户")
                return
                
            if self.is_running:
                messagebox.showwarning("警告", "机器人正在运行中，请先停止")
                return
                
            # 获取选中账户的信息
            item = selected_items[0]
            values = self.account_tree.item(item, 'values')
            account_index = int(values[0]) - 1  # 序号从1开始，索引从0开始
            
            # 验证输入
            if not self.validate_inputs():
                return
                
            self.log_to_gui(f"开始运行选中账户 (序号: {account_index + 1})", 'info')
            
            # 在新线程中运行选中的账户
            self.current_thread = threading.Thread(target=self.run_single_account_thread, args=(account_index,))
            self.current_thread.daemon = True
            self.current_thread.start()
            
        except Exception as e:
            self.log_to_gui(f"运行选中账户出错: {str(e)}", 'error')
            
    def show_account_details(self):
        """显示账户详细信息"""
        try:
            selected_items = self.account_tree.selection()
            if not selected_items:
                messagebox.showwarning("警告", "请先选择一个账户")
                return
                
            item = selected_items[0]
            values = self.account_tree.item(item, 'values')
            
            details = f"""账户详细信息:
            
序号: {values[0]}
钱包地址: {values[1]}
每日签到: {values[2]}
游戏活动: {values[3]}
AI聊天: {values[4]}
积分: {values[5]}
最后活动时间: {values[6]}"""
            
            messagebox.showinfo("账户详细信息", details)
            
        except Exception as e:
            self.log_to_gui(f"显示账户详细信息出错: {str(e)}", 'error')
            
    def run_single_account_thread(self, account_index):
        """在线程中运行单个账户"""
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行单个账户
            loop.run_until_complete(self.run_single_account_async(account_index))
            
        except Exception as e:
            self.log_to_gui(f"运行单个账户出错: {str(e)}", 'error')
            
    async def run_single_account_async(self, account_index):
        """异步运行单个账户"""
        try:
            # 加载账户
            account_file = self.account_file_var.get()
            with open(account_file, 'r') as f:
                account_keys = [line.strip() for line in f if line.strip()]
                
            if account_index >= len(account_keys):
                self.log_to_gui("账户索引超出范围", 'error')
                return
                
            key_entry = account_keys[account_index]
            wallet_address, masked_address = extract_wallet_address_info(key_entry)
            
            if not wallet_address:
                self.log_to_gui(f"❌ 无效的私钥: {masked_address}", 'error')
                return
                
            # 加载问题列表
            chat_questions = read_json_file_data("question_lists.json")
            if not chat_questions:
                self.log_to_gui("无法加载问题列表", 'error')
                return
                
            # 设置代理
            use_proxy = self.proxy_mode_var.get() == "private_proxy"
            rotate_proxy = self.rotate_proxy_var.get()
            
            if use_proxy:
                await self.task_manager.initialize_proxy_config(True)
                if not self.task_manager.proxy_collection:
                    self.log_to_gui("警告: 未找到代理，将不使用代理运行", 'warning')
                    use_proxy = False
                    
            self.log_to_gui(f"🔄 开始处理账户: {masked_address}", 'blue')
            
            # 设置请求头
            self.setup_headers(wallet_address)
            
            # 处理账户活动
            await self.process_account_activities(key_entry, wallet_address, 
                                                chat_questions, use_proxy, rotate_proxy)
            
            self.log_to_gui(f"✅ 账户处理完成: {masked_address}", 'success')
                    
        except Exception as e:
            self.log_to_gui(f"运行单个账户异常: {str(e)}", 'error')


if __name__ == "__main__":
    root = tk.Tk()
    app = ProtocolManagerGUI(root)
    root.mainloop() 