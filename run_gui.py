#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Warden Protocol 自动化机器人 GUI启动器
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui import ProtocolManagerGUI
    import tkinter as tk
    from tkinter import messagebox
    
    def main():
        try:
            # 创建主窗口
            root = tk.Tk()
            
            # 设置窗口图标（如果有的话）
            try:
                root.iconbitmap('icon.ico')
            except:
                pass
            
            # 创建GUI应用
            app = ProtocolManagerGUI(root)
            
            # 运行主循环
            root.mainloop()
            
        except Exception as e:
            messagebox.showerror("启动错误", f"无法启动GUI应用:\n{str(e)}")
            sys.exit(1)
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所有必需的依赖包:")
    print("pip install -r requirements.txt")
    sys.exit(1) 