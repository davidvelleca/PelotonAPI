# PelotonAPI
Python script to hit the Peloton API and download workout data &amp; metrics to an Excel file

# Disclaimer
This is one of my first Python projects.  Having said that, I'm sure there are better ways to do parts of what I'm trying to do.  

This is a work in progress, and is subject to change.  Feel free to reach out with any suggestions or questions.  Probably easiest to reach on Twitter - https://twitter.com/davidvelleca

# Overview
I was looking for a way to visualize my Peloton Workout data in Tableau.  Through some research, I came across mentions of a Peloton API for pulling this data, but found that Peloton do not have documentation of their API.  Fortunately, I stumbled across the GitHub repo referenced below in the Attribution that had really good documentation (at least as good as is possible when you have to document a complete unknown).  I used that documentation to make the following API calls

## Authentication
This section prompts the user for their Username or Email, Password and Excel Filename for exporting the final file.  Using the Username and PW, the script then authenticates the user session and uses this to hit privileged API endpoints.
```
user = input('Enter your username or email: ')
pw = input('Enter your password: ')
excel = input('Specify Excel filename & location: ')

#Authenticate the user
s = requests.Session()
payload = {'username_or_email': user, 'password':pw}
s.post('https://api.onepeloton.com/auth/login', json=payload)
```

## GET: User Id
This portion pulls the User ID from an API response that includes loads of summary data about the user.
```
#Get User ID to pass into other calls
me_url = 'https://api.onepeloton.com/api/me'
response = s.get(me_url)
apidata = s.get(me_url).json()

#Flatten API response into a temporary dataframe
df_my_id = json_normalize(apidata, 'id', ['id']) 
df_my_id_clean = df_my_id.iloc[0]
my_id = (df_my_id_clean.drop([0])).values.tolist()
```

## GET: Workout, Ride & Instructor details
Leveraging the User ID returned in the prior call, this pulls back LOADS of metadata on Workouts, Rides and Instructors.  Workouts and Rides are a bit confusing, so think of it like this:

  - A Workout is any Peloton 'Ride' you do (on the Bike, Tread or Peloton Digital), and is tied to your effort.
  - A Ride is the details of the Class (once again on any device - Bike, Tread or Peloton Digital).  The data pulled in this call are not tied to your effort.
```
url = 'https://api.onepeloton.com/api/user/{}/workouts?joins=ride,ride.instructor&limit=250&page=0'.format(*my_id)
response = s.get(url)
data = s.get(url).json()
```

## GET: Workout Metrics
The script then pulls a list of Workout IDs from the dataframe resulting from the prior call.  Then, this list is passed into the Workout endpoint to pull back some average and total metrics on the user's workout.  Note that this section could be updated to pull in the data that is presented in the line charts on the Bike/Tread/App to show things like cadence, resistance, etc.  If you do that, I'd recommend changing the 'every_n' parameter on the API URL to be more frequent.  This is a value in seconds that I've limited to 5 minutes as that is the shortest Ride possible.
```
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
```

# Attribution
I heavily leveraged the API documentation at https://github.com/geudrik/peloton-client-library/blob/master/API_DOCS.md to work through the API. 
