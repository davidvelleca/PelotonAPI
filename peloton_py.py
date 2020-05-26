import pandas as pd
import requests
import json
from pandas.io.json import json_normalize

user = input('Enter your username or email: ')
pw = input('Enter your password: ')
excel = input('Specify Excel filename & location: ')

#Authenticate the user
s = requests.Session()
payload = {'username_or_email': user, 'password':pw}
s.post('https://api.onepeloton.com/auth/login', json=payload)

#Get User ID to pass into other calls
me_url = 'https://api.onepeloton.com/api/me'
response = s.get(me_url)
apidata = s.get(me_url).json()

#Flatten API response into a temporary dataframe
df_my_id = json_normalize(apidata, 'id', ['id']) #['average_summaries'])
df_my_id_clean = df_my_id.iloc[0]
my_id = (df_my_id_clean.drop([0])).values.tolist()

#API URL - 
url = 'https://api.onepeloton.com/api/user/{}/workouts?joins=ride,ride.instructor&limit=250&page=0'.format(*my_id)
response = s.get(url)
data = s.get(url).json()

#Flatten API response into a temporary dataframe
df_workouts_raw = json_normalize(data['data'])

#Keep only necessary columns as a new pandas dataframe - this list can be modified based on the user's 
#preference.  Right now, primarily excluding duplicated columns, excess ID columns, and social media
#columns for the Instructors
df_workouts = df_workouts_raw.drop(df_workouts_raw.columns[[4, 5, 11, 13, 
15, 16, 17, 20, 24, 25, 27, 28, 29, 31, 32, 33, 35, 37, 39, 40, 41, 42, 
43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 59, 60, 63, 
64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 76, 77, 78, 79, 80, 81, 82, 
83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 96, 97, 98, 99, 100, 103, 
105, 106, 107, 108]], axis = 1)

#Print Message Workout Data Complete
print('Workout Data processing complete')

#Create Dataframe of Workout IDs where the workout has metrics
df_workout_ids_raw = df_workouts.filter(['id', 'fitness_discipline'], axis=1)
df_workout_ids = df_workout_ids_raw[df_workout_ids_raw['fitness_discipline'].isin(['cycling', 'walking'])]
df_workout_ids.drop(columns =['fitness_discipline'])

#Define the imputs for the for loop
workout_ids = df_workout_ids.values.tolist()
workout_ids2 = [i[0] for i in workout_ids]
df_workout_metrics = pd.DataFrame([])

for workout_id in workout_ids2:
     response2 = s.get('https://api.onepeloton.com/api/workout/{}/performance_graph?every_n=300'.format(workout_id))
     data2 = response2.json()
     #Flatten API response into a temporary dataframe - have to handle the avg and tot separately due to 
     #the way that this API response is structured - each row is another timestamp of metrics for the ride
     #in this case every 300 seconds and interspersed with this is the summary data - both total and average
     df_avg_raw = json_normalize(data2['average_summaries'])
     df_tot_raw = json_normalize(data2['summaries'])
     #Transpose the average and total data to a single row
     df_avg_stg = df_avg_raw.T
     df_tot_stg = df_tot_raw.T
     #Cleanup the data - remove a garbage column and unnecessary rows
     df_avg_stg.columns = df_avg_stg.iloc[0]
     df_tot_stg.columns = df_tot_stg.iloc[0]
     df_avg = df_avg_stg.drop(['display_name', 'slug', 'display_unit'])
     df_tot = df_tot_stg.drop(['display_name', 'slug', 'display_unit'])
     #Add the workout ID back into the data
     df_avg['id'] = workout_id
     #Merge the two dataframes - avg and tot
     df_metrics = pd.concat([df_avg,df_tot], axis = 1)
     #Append each run through the loop to the dataframe
     df_workout_metrics = df_workout_metrics.append(df_metrics, sort=False)

#Print Message Workout Metrics Complete
print('Workout metrics processing complete')

#Left outer join of the Workout Data and Metrics
df_peloton_final = df_workouts.merge(df_workout_metrics, left_on='id', right_on='id', how='left')

#Export the merged dataframes to Excel
df_peloton_final.to_excel(excel)

#Success!
print('Full data exported to Excel!')