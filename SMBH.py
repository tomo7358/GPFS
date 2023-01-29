import camelot
import pandas as pd
import sys
import numpy as np





class Markbook():
    def __init__(self):
        self.df = None
        self.grade_categories = None
        self.unit_categories = None

    def extract_tables(self,file_path):
        # Read the PDF file and extract the tables
        try:
            tables = camelot.read_pdf(file_path)
        
            # Create a list to store the table data
            table_data = []

            # Iterate through each table
            for table in tables:
                # Get the table data as a Pandas DataFrame
                df = table.df

                # Add the DataFrame to the list
                table_data.append(df)
        #exeption handling that prints the exception and exits the program
        except Exception as e:
            print(e)
            sys.exit(1)
        # Concatenate all of the DataFrames into a single DataFrame
        self.df = pd.concat(table_data)

        # Rename the columns
        self.df.columns = ['Task', 'Mark', 'Out Of', 'Weight', 'Class Average']

        # Remove the first row (which contains the column names)
        self.df = self.df.drop(0)
        self.df = self.df.drop(1)
        # Convert the 'Mark' and 'Out Of' columns to numeric values
        self.df['Mark'] = pd.to_numeric(self.df['Mark'], errors='coerce')
        self.df['Out Of'] = pd.to_numeric(self.df['Out Of'], errors='coerce')

        # Drop the 'Class Average' column
        self.df = self.df.drop(columns='Class Average')

        # Remove newline characters from the 'Task' column
        self.df['Task'] = self.df['Task'].str.replace('\n', ' ')

        # Extract the dates from the 'Task' column
        self.df['Date'] = self.df['Task'].str.extract(r'\((.*)\)')

        # Remove the dates from the 'Task' column
        self.df['Task'] = self.df['Task'].str.replace(r'\(.*\)', '')
        return self.df
    
    def calculate_marks(self):
        # replace the "NaN" strings with the NaN value
        self.df = self.df.replace("NaN", np.nan, inplace=False)
        # iterate through the rows of the dataframe
        for index, row in self.df.iterrows():
            # if the mark is not NaN
            if not pd.isnull(row["Mark"]):
                # calculate the mark as a percentage of the Out Of value
                # (casting one of the values to float to perform floating point division)
                mark=float(row["Mark"])
                denominator=float(row["Out Of"])
                calculated_mark = float(round((mark/denominator)*100,2))
                # store the calculated mark in the new column
                self.df.at[index, "Calculated Mark"] = calculated_mark
        self.df = self.df.drop(columns='Mark')
        self.df.drop("Out Of", axis=1, inplace=True)
        # return the modified dataframe
        return self.df


    def identify_nhi(self,nhi_list):
        # create a new column in the dataframe to store the calculated marks
        self.df["Calculated Mark"] = 0
        # Iterate through the rows of the dataframe
        for index, row in self.df.iterrows():
            # Check if the mark is NaN
            if pd.isnull(row["Mark"]):
                 # Check if the task is in the list of NHI's
                if row["Task"] in nhi_list:
                    self.df.at[index, "Mark"] = 0
                    self.df.at[index, "Calculated Mark"] = "NHI"
                else:
                    self.df.at[index, "Calculated Mark"] = "PASS"
        return self.df
    
    def calculate_markbook(self):
        markbook=self.df
        weighted_avg=None
        current_grade=[]
        current_weight = []

        #function that finds the grade group and unit for each task
        def identify_root_task(markbook):
            #find the first occurence of each grade group and unit and add them to a list
            grade_categories = []
            unit_categories = []
            #iterate through each task
            for task in markbook["Task"].unique():
                #if the task is a grade category, add it to the list
                if task in markbook["Grade Group"].unique():
                    grade_categories.append(task)
                #if the task is a unit, add it to the list
                elif task in markbook["Unit"].unique():
                    unit_categories.append(task)     
            return (grade_categories, unit_categories)
        #function that checks if a task has been repeated and is a unit or grade category
        def check_repeat(markbook,grade_categories,unit_categories):
            #loop through each task
            for task in markbook["Task"].unique():
                #check if the task is a grade category or unit
                if task in grade_categories or task in unit_categories:
                     if markbook[markbook["Task"] == task].shape[0] > 1:
                        markbook.loc[markbook[markbook["Task"] == task].index[0], "Task"] = task + "."
            return(markbook)

        #call the function to find the grade group and unit for each task
        grade_categories, unit_categories = identify_root_task(markbook)
        check_repeat(markbook,grade_categories,unit_categories)
        #if the task is a grade category or unit set the calculated mark to NaN
        markbook["Calculated Mark"] = markbook.apply(lambda row: np.nan if row["Task"] in grade_categories or row["Task"] in unit_categories else row["Calculated Mark"], axis=1)
        #for loop that iterates through each grade group and unit
        for grade_group in markbook["Grade Group"].unique():
            current_grade = []
            current_weight = []
            weighted_avg=None
            #loop for each unit
            for unit in markbook["Unit"].unique():
                #for loop for each task in unit
                for task in markbook[(markbook["Unit"] == unit)]["Task"].unique():
                    #check if the task is a grade category or unit
                    if task in grade_categories or task in unit_categories:
                        continue

                    #append tasks calculated mark to list
                    #if the task is not a grade category or unit, append the calculated mark to the list aslong as it is not an PASS
                    if markbook[(markbook["Task"] == task) & (markbook["Unit"] == unit)]["Calculated Mark"].values[0] != "PASS":
                        current_grade.append(float(markbook[(markbook["Task"] == task) & (markbook["Unit"] == unit)]["Calculated Mark"].values[0]))
                        current_weight.append(float(markbook[(markbook["Task"] == task) & (markbook["Unit"] == unit)]["Weight"].values[0]))     
                #if the list is not empty, calculate the weighted average
                if current_grade != [] and current_weight != []:
                    #calculate the grade for the unit using this function sum(mark * weight for mark, weight in zip(marks, weights)) / sum(weights)
                    total_weight = sum(current_weight)
                    #calculate the weighted average for the unit
                    for grade, weight in zip(current_grade,current_weight):
                        #if the weight is 0, set the calculated mark to 0
                        weighted_avg = round(sum(grade * weight for grade, weight in zip(current_grade, current_weight)) / sum(current_weight),2)
                    #set current grade and weight to empty lists
                    current_grade = []
                    current_weight = []
                # if the weighted average is not none, set the calculated mark for the unit to the weighted average
                if weighted_avg != None:
                    #for loop for each task in unit
                    for task in markbook[(markbook["Unit"] == unit)]["Task"].unique():
                        #check if the task is a grade category or unit
                        if task in unit_categories:
                            #set the calculated mark to the weighted average
                            markbook.loc[(markbook["Task"] == task) & (markbook["Unit"] == unit), "Calculated Mark"] = weighted_avg
                    #set the weighted average to none     
                    weighted_avg = None
            
            #check if grade group is not []
            if grade_categories != []:
                current_grade=[]
                current_weight=[]
                #loop through each unit in grade group
                for unit in markbook[(markbook["Grade Group"] == grade_group)]["Unit"].unique():
                    
                    #check to make sure its assingned a unit 
                    if unit == None:
                        continue
                    elif unit == "Class":
                        continue

                    else:
                        if markbook[(markbook["Unit"] == unit)]["Calculated Mark"].values[0] != "PASS" and pd.isnull(markbook[(markbook["Unit"] == unit)]["Calculated Mark"].values[0]) == False:
                            current_weight.append(int(markbook[(markbook["Unit"] == unit)]["Weight"].values[0]))
                            current_grade.append(int(markbook[(markbook["Unit"] == unit)]["Calculated Mark"].values[0]))
                            
                #calculate the weighted average for the grade group
                if pd.isnull(markbook[(markbook["Unit"] == unit)]["Calculated Mark"].values[0]) == False:      
                    #calculate the weighted average for the grade group
                    weighted_avg = round(sum(grade * weight for grade, weight in zip(current_grade, current_weight)) / sum(current_weight),2)
                    #for the 1st task in the current grade group set the calculated mark to the weighted average
                    for task in markbook[(markbook["Grade Group"] == grade_group)]["Task"].unique():
                        if task in grade_categories:
                            markbook.loc[(markbook["Task"] == task) & (markbook["Grade Group"] == grade_group), "Calculated Mark"] = weighted_avg
                            break
        
            #if the list is not empty, calculate the weighted average of the whole class
            else:
                #get each unit in dataframe
                for unit in markbook["Unit"].unique():
                    #get the weight and calculated mark for each unit if the weight of that unit is not 0
                    if int(markbook[(markbook["Unit"] == unit)]["Weight"].values[0]) != 0:
                        #check to see if unit has a calculated mark of PASS or NaN
                        if markbook[(markbook["Unit"] == unit)]["Calculated Mark"].values[0] != "PASS" and pd.isnull(markbook[(markbook["Unit"] == unit)]["Calculated Mark"].values[0]) == False:
                            #append the weight and calculated mark to the list
                            current_weight.append(float(markbook[(markbook["Unit"] == unit)]["Weight"].values[0]))
                            current_grade.append(float(markbook[(markbook["Unit"] == unit)]["Calculated Mark"].values[0])) 
                #calculate avg for class
                weighted_avg = round(sum(grade * weight for grade, weight in zip(current_grade, current_weight)) / sum(current_weight),2)
        current_grade=[]
        current_weight=[]
        if grade_categories != []:
        #loop through each grade category
            for group in grade_categories:
                #get the calculated mark and weight for each grade category where the grade catagoery is the 1st item with the grade group name and the mark and weight are not NaN or None
                for mark, weight in zip(markbook[(markbook["Grade Group"] == group) & (markbook["Task"] == group)]["Calculated Mark"].values, markbook[(markbook["Grade Group"] == group) & (markbook["Task"] == group)]["Weight"].values):
                    if mark != "PASS" and pd.isnull(mark) == False:
                        current_grade.append(float(mark))
                        current_weight.append(float(weight))
            #calculate avg for the whole class
            weighted_avg = round(sum(grade * weight for grade, weight in zip(current_grade, current_weight)) / sum(current_weight),2)


        self.df=markbook
        return markbook, weighted_avg

    def data(self):
        return(self.df)