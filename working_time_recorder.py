from datetime import datetime, timedelta, date
import time, os
import logging

import tkinter as tk
import pandas as pd
import openpyxl


class Timer:
    def __init__(self, master):
        self.master = master
        self.master.title("Working Timer")
        self.master.geometry("500x200")
        self.master.resizable(False, False)
        #self.master.configure(background='white')

        self.current_time = tk.Label(self.master, text=self.get_current_time(), font=("Arial", 20))
        self.current_time.pack(pady=10)
        
        self.timer_label = tk.Label(self.master, text="00:00:00", font=("Arial", 30))
        self.timer_label.pack(pady=10)
        
        self.start_button = tk.Button(self.master, text="start Working", bg="green", fg="pink", font=("Arial", 14), command=self.start_timer)
        self.start_button.pack(side="left", padx=10)
        
        self.stop_button = tk.Button(self.master, text="Stop Working", bg="red", fg="pink", font=("Arial", 14), state="disabled", command=self.stop_timer)
        self.stop_button.pack(side="right", padx=10)
        
        self.export_button = tk.Button(self.master, text="Export", bg="black", fg="pink", font=("Arial", 14), command=self.export_timesheet)
        self.export_button.pack(side="bottom", padx=10)

        self.timestamp_file = 'log.txt'
        
        if not os.path.exists(self.timestamp_file):
            os.system(f'touch {self.timestamp_file}')
            self.last_log_date = None
        else:
            with open(self.timestamp_file) as f:
                try:
                    last_timestamp = (f.read()).split()[-1]
                    self.last_log_date = last_timestamp.split('T')[0]
                except Exception:
                    self.last_log_date = None

        self.start_time = None
        self.elapsed_time = timedelta()
        self.timer_running = False
        self.update_clock()
    
    def get_current_time(self):
        return datetime.now().strftime("%A, %B %d %Y %H:%M:%S")
    
    def update_clock(self):
        self.current_time.config(text=self.get_current_time())
        if self.timer_running:
            self.elapsed_time = datetime.now() - self.start_time
            self.timer_label.config(text=str(self.elapsed_time).split('.')[0])
        self.master.after(1000, self.update_clock)
    
    def start_timer(self):
        if not self.timer_running:
            self.start_time = datetime.now()
            self.timer_running = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.log_start_time()
    
    def stop_timer(self):
        if self.timer_running:
            self.timer_running = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.log_stop_time()

    def export_timesheet(self):
        with open(self.timestamp_file, 'r') as f:
            raw_timestamps = f.read()
        if len(raw_timestamps) == 0:
            raise Exception('No Data to Export')

        self.process_raw(raw_timestamps)

    def process_raw(self, raw_timestamps):
        alist = raw_timestamps.split('\n')
        self.row = [x.split('T')[0] for x in alist]
        longest_row = max([len(x.split()) for x in alist])

        # assumble the titles in table
        self.coloum = []
        self.coloum += [['Start Working']]
        self.coloum += [['Stop Breaking and start working', 'Total for Break'] if x%2 else ['Stop Working and start Breaking'] for x in range(longest_row - 2)]
        self.coloum += [['Stop Working']]
        self.coloum += [['Daily Resting Total','Daily Working Total']]
        logging.warning(self.coloum)

        date_set = self.assumble_array(alist, longest_row)
        
        df = pd.DataFrame(date_set,
                          index=self.row, columns=[i for x in self.coloum for i in x])
        
        df.to_excel('timesheet.xlsx', sheet_name=f'{self.row[0]} -- {self.row[-1]}')

    def assumble_array(self, data, max_len):

        time_string_format = '%Y-%m-%dT%H:%M:%S.%f'
        data_set = []

        for idx in range(len(data)):
            timestamps = data[idx].split()
            time_stamps_list = list(map(lambda x: datetime.strptime(x, time_string_format), timestamps))
            logging.debug(time_stamps_list)
            
            alist = time_stamps_list[1:-1:]
            start_rest = alist[0::2]
            stop_rest = alist[1::2]

            if not len(start_rest) == len(stop_rest) or len(timestamps) == 1:
                logging.error(f'Found missing time stamp at line {idx+1} in log.txt')
                logging.warning('Try to export possible data...')

            rest = [stop_rest[i] - start_rest[i] for i in range(len(stop_rest))]
            logging.debug(max_len)
            sum_of_rest = sum(rest, timedelta())
            #print(sum_of_rest)
            logging.debug(sum_of_rest)
            diff = list(map(str, rest))
            logging.debug(alist)
            logging.debug(diff)

            list_of_rest = timestamps[1:-1:]
            list_of_rest_with_duration = [list_of_rest[i+i:(i+1)*2]+[diff[i]] for i in range(len(diff))]
            
            sub_list = []
            sub_list += [timestamps[0]]
            sub_list += [i for x in list_of_rest_with_duration for i in x]
            sub_list += [timestamps[-1]]
            sub_list += [''] * (max_len + (max_len - 2) // 2 - len(sub_list))
            rested = str(sum_of_rest).split('.')[0]
            sub_list += [rested]
            worked = str(time_stamps_list[-1] - time_stamps_list[0] - sum_of_rest).split('.')[0]
            sub_list += [worked]
            day = timestamps[0].split('T')[0]
            started = str(timestamps[0].split('T')[1]).split('.')[0]
            logging.warning(f'{day} -- {started} -- {rested} -- {worked}')
            data_set.append(sub_list)
        
        logging.debug(data_set)
        return data_set

    def log_start_time(self):
        self.log_file = open(self.timestamp_file, "a")
        log_date = datetime.now().date()

        if str(log_date) != str(self.last_log_date) and self.last_log_date != None:
            self.log_file.write("\n")
        self.log_file.write(datetime.now().isoformat() + " ")
        self.last_log_date = log_date
        self.log_file.close()
    
    def log_stop_time(self):
        self.log_file = open(self.timestamp_file, "a")
        self.log_file.write(datetime.now().isoformat() + " ")
        self.log_file.close()

root = tk.Tk()
timer = Timer(root)
root.mainloop()
