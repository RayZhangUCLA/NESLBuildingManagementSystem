document.addEventListener('DOMContentLoaded',domloaded,false);
function domloaded(){
	const api_gethistory = 'http://128.97.93.240:7000/data_visualization/dashboard/history_data?uuid=';
	const api_getcurrent = 'http://128.97.93.240:7000/data_visualization/dashboard/current_data?uuid=';
	const api_getPropotions = 'http://128.97.93.240:7000/data_visualization/dashboard/proportions?uuid=';
	const api_getEnergy = 'http://128.97.93.240:7000/data_visualization/dashboard/energy?uuid=';
	const api_get_query_smap = 'http://128.97.93.240:7000/data_visualization/dashboard/smap_query';
	const api_get_query_db = 'http://128.97.93.240:7000/data_visualization/dashboard/db_query';
	//api_get_query_db + uuid + length + db = hours
	const water_uuid = '09bb4086-0335-26b2-1749-a489e7718337';
	const power_uuid = '6a6e1be3-2315-f849-f02c-adea4fe29099';
	const water_mul = 3600;
	const power_mul = 1;
	var multiplier=0;
	var name = $('#today_till_now').attr('data-name');
	var length = 0;
	var db='hours';
	var till_now_amount = 0;
	var till_now_dollar = 0;
	var refresh_rate = 10000;
	//get data each 10seconds
	var unit="";
	var till_now_unit='';
	var api_get_query="";
	var window_size=1;
	var window_unit='hour';
	var running_total = 0;
	var cur_time = new Date().getTime();
	var start_time=0;	
	var info_string='';

	$(function(){
		console.log("**** stat data name:" + name);

		if (name == 'power'){
			uuid = power_uuid;
			unit = 'W';
			info_string='Today to now: ';
			till_now_unit = ' kWhr';
			multiplier = power_mul;
		}else if(name == 'water'){
			uuid = water_uuid;
			unit = 'cm^3/s';
			info_string='Today to now: ';
			till_now_unit = ' Liters';
			multiplier = water_mul;
		}

		/*function jsonSuccess(data){
			console.log("**** stat data: RAW" + JSON.stringify(data));
			function get_till_cur_hr_sum(){
				//get 1 data point per hour
				//console.log("url = " + url);
				$.each(data.data, function(i,val){
					//console.log("**** stat: each data point " + JSON.stringify(val));
					running_total = running_total + val[1];
				});
				console.log("**** stat; total from db"+running_total);
				return running_total;
			}

			console.log("**** stat till now url: "+ url);
			till_now_amount = get_till_cur_hr_sum();
			till_now_amount = till_now_amount/1000;
			//energy consumption of the day till the beginning of current hour in kWhr
			//or water
			console.log('**** stat; DB till this hour: ' + till_now_amount);
			
			function get_cur_hr_till_now(){
				//using smap
				console.log("**** stat; asking smap for data");
				var seconds_total = 0;
				var url_seconds = '';
				start_time = parseInt(cur_time/60/60/1000)*60*60*1000;
				url_seconds = api_get_query_smap+'?uuid='+uuid+'&starttime='+start_time+'&window_size=1'+'&window_unit=second';
				console.log("**** stat; smap url: "+ url_seconds);
				console.log("**** stat; smap start time: " + new Date(start_time));
				$.getJSON(url_seconds, function (data){
					console.log('**** stat; smap data length: '+data.data.length);
					if (data.data.length<1){
						console.log("**** stat; No smap live data for the hour");
						return 0;
					}
					console.log('**** stat; smap data points RAW' + JSON.stringify(data));
					$.each(data.data, function(i,val){
						seconds_total += val[1];
					});
					seconds_total = seconds_total/data.data.length;
					console.log("**** stat; seconds_total"+ seconds_total);
					seconds_total = seconds_total/1000;
					console.log("hourly total: " + seconds_total);
					till_now_amount += seconds_total;
					$("#today_till_now").text(info_string+ parseFloat(till_now_amount.toFixed(2)) + till_now_unit);
					
				});
				//total of the hour by seconds					
				//unit of kWhr

			}
			//energy consumption of the hour till this moment

			get_cur_hr_till_now();
			//till_now_amount = multiplier*till_now_amount;
			console.log('**** stat; till now with smap: '+ parseFloat(till_now_amount.toFixed(3))+ " -- multiplier: " + multiplier);
			console.log("**** stat: "+ "start time:  "+ new Date(start_time/1000) + "  current time: "+ new Date(cur_time)+ "  till now amount " + till_now_amount);
			function computeTillNow(){
				function get_current_val() {
					$.get(api_getcurrent + uuid, function(data, status){
						last_data = series.data[series.data.length-1];
						console.log("data: "+ JSON.stringify(data));
						//console.log("last_data: " +JSON.stringify(last_data));
						last_timestamp=last_data['x'];
						data = $.parseJSON(data);
						console.log("data.data:  "+ JSON.stringify(data.data));
						if(data.data[0][0] > last_timestamp){
							running_total += data.data[0]*10/3600;
							//series.addPoint(data.data[0], true, true);	
						}
					});
					console.log("**** stat; today till now updateing");
					//units of kWhr
					$("#today_till_now").text("New data in");
					//$('#today_till_now').innerHTML = $('#today_till_now').innerHTML + stringify(till_now_amount)+" kWhr";
					//till_now_dollar = till_now_amount*0.12;
					console.log("till now: "+ till_now_amount);
					//till now amount has to be in kWhr
					//$('today_till_now_dollar').innerHTML = $('today_till_now_dollar').innerHTML +stringify(till_now_dollar)+ " Dollars";
				}
				setTimeout(get_current_val, refresh_rate);

			}
			//setTimeout(computeTillNow, refresh_rate);
			
		}//end jsonSuccess

		start_time = cur_time - ((cur_time-7*60*60*1000) % (24*60*60*1000));
		length = parseInt(((cur_time-7*60*60*1000)%(24*60*60*1000))/(60*60*1000));			
		url = api_get_query_db + '?uuid=' + uuid + '&length='+length+'&db=hours';
		//url= api_get_query_smap + '?uuid='+ uuid +'&starttime='+ start_time +'&window_size=' + window_size + '&window_unit=' + window_unit;
		console.log("**** Stat URL: " + url);
		//$.getJSON(url,jsonSuccess);*/
		function getUnitMultiplier() {
			if (name == "power") {
				return 1/3600000;
			}
			else if (name == "water") {
				return 1/1000;
			}
		}
		function getUnits() {
			if (name == "power") {
				return "kWh"
			}
			else if (name == "water") {
				return "Liters"
			}
		}
		var date_obj = new Date()
                var date_num = date_obj.getDate()
                var hour_num = date_obj.getHours()
                var time_ms = date_obj.getTime()	

		function getHourTotal(uuid, total_except_current_hour) {
                        function second_smap_query_success(data) {
                                var total_current_hour = total_except_current_hour;
                                $.each(data.data, function(i, val) {
                                        total_current_hour += val[1];
                                });

                                var total_units = getUnitMultiplier() * total_current_hour;
                                $("#today_till_now").text(parseFloat(total_units.toFixed(2)) + " " + getUnits());
                        }
                        // our starttime is the last hour boundary
                        var starttime = time_ms - (time_ms % (60 * 60 * 1000));
                        var endtime = time_ms;
                        console.log("starttime: " + starttime + " endtime: " + endtime)
                        var url_second_query = api_gethistory + "?uuid=" + uuid + "&starttime=" + starttime + "&endtime=" + endtime;
                        $.getJSON(url_second_query, second_smap_query_success);
                }

                function getDayTotal(uuid) {
                        function hours_db_query_success(data) {
                                var total_except_current_hour = 0;
                                $.each(data.data, function(i, val) {
                                        // val is the average reading for the hour, so
                                        // multiply by the number of seconds in an hour
                                        // to get the total of all the readings
                                        total_except_current_hour += val[1] * 60 * 60;
                                });
                                getHourTotal(uuid, total_except_current_hour);
                        }
                        // get all the hours today except the current hour
                        var hours_to_get = hour_num - 1;
                        var url_hour_query = api_get_query_db + "?uuid=" + uuid + "&db=hours&length=" + hours_to_get;
                        $.getJSON(url_hour_query, hours_db_query_success);
                }
		getDayTotal(uuid)



		url = api_get_query_db + '?uuid=' + uuid + '&length=48'+'&db=hours';
		console.log("**** stat; yesterday's url: "+url);
		$.getJSON(url,function(data){
			//var yesterday_val = data.data[0][1]*24/1000;
			//console.log("**** stat; yesterday's data: "+ yesterday_val);
			//$("#daily_avg").text("Yesterday: " + parseFloat(yesterday_val.toFixed(2)) + till_now_unit);
			today_day_num = new Date(cur_time).getDay()
			yesterdays_total = 0
			hour_count = 0
			for (i = 0; i < data.data.length; i++) {
				ts = data.data[i][0]
				rd = data.data[i][1]
				date_obj = new Date(ts)
				day_num = date_obj.getDay()
				if (today_day_num - day_num == 1 || (today_day_num == 0 && day_num == 6)) {
					yesterdays_total += rd * 60 * 60	
					hour_count += 1
				}
			}
			console.log("yesterdays hour count: " + hour_count)
			var yesterdays_total_multiplier = getUnitMultiplier();
			
			var yesterdays_total_final = yesterdays_total * yesterdays_total_multiplier;
			$("#daily_avg").text(parseFloat(yesterdays_total_final.toFixed(2)) + till_now_unit);
		});
				
		

	});
	//end function()

}
//end of domloaded
