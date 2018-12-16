from HTMLParser import HTMLParser
import requests

#HTML PARSER CLASS
class MyHTMLParser(HTMLParser):
    start_tags = []
    all_data = []
    def handle_starttag(self, tag, attrs):
        temp = {
            'typ': 'start',
            'data': tag
        }
        self.all_data.append(temp)
        self.start_tags.append(tag)


    end_tags = []
    def handle_endtag(self, tag):
        temp = {
            'typ': 'end',
            'data': tag
        }
        self.all_data.append(temp)
        self.end_tags.append(tag)

    data = []
    def handle_data(self, data2):
        temp = {
            'typ': 'data',
            'data': data2
        }
        self.all_data.append(temp)
    	self.data.append(data2)



def parse_row(row):
#Function takes in a row, which is a list of lists with each row
#Function assumes that all neccessary information is included in td tags
#Format of 
# | CAS PS101 A2 | General Psych | 0.0 | Discussion | 0 | STH | 318 | Wed | 9:05am | 9:55am | Class Full
#                     Tompson     
# character '|' represents information within td tags
#Assumption: each row is in this fromat with 11 td starts and ends
#Also checks for break statements since some information have underneath information
    i = 0
    parsed_row = []
    while (i < len(row)):
        temp = row[i]
        if (temp['data'] == 'td' and temp['typ'] == 'start'):           #if found start td
            temp_dat = []
            while not(temp['data'] == 'td' and temp['typ'] == 'end'):   #while i havent found end td
                if (temp['typ'] == 'data'):                              #if is data type
                    temp_dat.append(temp['data'])                       #add to temp_dat
                if (temp['data'] == 'br'):                              #if there is a break, add it
                    temp_dat.append(temp['data'])
                i+=1
                if (i >= len(row)):
                    break
                temp = row[i]
            parsed_row.append(temp_dat)
        i+=1
    return parsed_row       #return list of lists




def seperate_data(inp):
#Function takes a list of information as input, ASSUMING it has a break tag in between
#function will spit first as a list of the info before break and rest which has info after break
    i=0
    first = []
    rest = []
    start_rest = 0
    while i < len(inp):
        dat = inp[i]
        if (dat == 'br'):
            start_rest = 1
        if (start_rest == 0):
            first.append(dat)
        else:
            if (dat != 'br'):
                rest.append(dat)
        i+=1
    return first, rest;


def remove_breaks(inp):
#Function serves to remove break statements from "Notes" section on Student Link
    notes = ''
    for i in inp:
        if (i != 'br'):
            notes = notes + i + ' '
    notes = notes[:-1]
    return notes



def print_nice(inp):
    print(inp['course'])
    print(inp['semester'])
    print("Sections:")
    for i in inp['classes']:
        print(i)


def get_classes_of_onepage(year, semester, college, dept, course, section):
#function takes in a year, a semester, college, dept, and course and returns 
#dictionary with keys "semester", "course", "classes", where value of "classes" 
#is a list of all sections, read by Student Link
    #both college and dept need to be upper case
    college = college.upper()
    dept = dept.upper()
    
    #define a MyHTMLParser object
    parser = MyHTMLParser()
    url = 'https://www.bu.edu/link/bin/uiscgi_studentlink.pl/1543352283?ModuleName=univschr.pl&SearchOptionDesc=Class+Number&SearchOptionCd=S&KeySem=' + year + '4&ViewSem=' + semester 
    url = url + '+' + year + '&College=' + college + '&Dept=' + dept + '&Course=' + course + '&Section='
    if (section):
        url = url + section
    #download webpage
    r = requests.get(url)
    print "url is ", url                   #Uncomment this line to see URL for manual confirmation
    #feed text to parser
    parser.feed(r.text)

    i = 0
    all_rows = []
    while (i < len(parser.all_data)):
        current = parser.all_data[i]
        if (current['typ'] == 'start' and current['data'] == 'tr'):             #if we found a new row
            temp_row = []
            while not(current['typ'] == 'end' and current['data']== 'tr'):     #while i havent found the end tag
                temp_row.append(current)
                i+=1
                current = parser.all_data[i]
            #Out of while loop which means we have reached the end tag of row
            all_rows.append(temp_row)
        i+=1

    all_parsed_rows = []
    for sup in all_rows:
        row = parse_row(sup)
        row_without_empty = [x for x in row if x != []]
        if len(row)==13:
            all_parsed_rows.append(row_without_empty)
    #Final structure will be a dictionary with keys: "semester", "course", "classes"
    #where value of "classes" is a list of all sections with information
    all_classes = {
                "semester": semester + year,
                "course": college + dept + course
            }
    all_classes["classes"] = []

    for temp in all_parsed_rows:
        temp_class = temp[0]
        if (temp_class[0] == college and temp_class[1] == (dept + course)):
            section = temp_class[2]
            name, prof = seperate_data(temp[1])
            name_str = ''
            for i in name:
                name_str = name_str + i + ' ' 
            credits = temp[2][0]
            type_class = temp[3][0]
            seats = temp[4][0]
            try:
                where = temp[5][0] + temp[6][0]
                days = temp[7][0]
                start_time = temp[8][0]
                end_time = temp[9][0]
            except:
                where = temp[5][0]
                days = ''
                start_time = ''
                end_time = ''
            try: 
                notes_list = temp[10]
                notes = remove_breaks(notes_list)
            except:
                notes = "No Notes"
            class_str = {
                    "section": section,
                    "name": name_str[:-1],
                    "professor": prof[0],
                    "credits": credits,
                    "type": type_class,
                    "room": where,
                    "day": days,
                    "start_time": start_time,
                    "end_time": end_time,
                    "notes": notes,
                    "seats": seats
            }

            all_classes['classes'].append(class_str)
    return all_classes


def get_all_sections(year, semester, college, dept, course, section):
    res = get_classes_of_onepage(year, semester, college, dept, course, [])
    last_sec = res["classes"][-1]["section"]
    last_index = len(res["classes"])-1
    full_res = get_classes_of_onepage(year, semester, college, dept, course, last_sec)
    del full_res["classes"][last_index]
    return full_res


year = '2019'
semester = 'Spring'
college = 'hub'         
dept = 'xc'             
course = '433'
a = get_all_sections(year, semester, college, dept, course, [])
print_nice(a)

# print_nice(res2)
