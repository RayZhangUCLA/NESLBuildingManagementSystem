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
	const water_price =1.237/2831.68;
	const power_price =0.12;
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
	var id='';
	var bill_id='';
	

	$(function(){
		var date_obj = new Date()
		var date_num = date_obj.getDate()
		var hour_num = date_obj.getHours()
		var time_ms = date_obj.getTime()

		console.log("**** overview data name:" + name);
		
		// gets the TOTAL of all the readings for the current hour
		function getHourTotal(uuid, total_except_current_hour, display_opts) {
			function second_smap_query_success(data) {
				console.log("id: " + display_opts.unit_id + " second smap: " + JSON.stringify(data))
				var total_current_hour = total_except_current_hour;
				$.each(data.data, function(i, val) {
					total_current_hour += val[1];
				});
				
				var total_units = display_opts.unit_multiplier * total_current_hour;
				var bill_amt = display_opts.price_per_unit * total_units;
				console.log("overall total: " + total_units + " " + display_opts.unit_id)
				$(display_opts.unit_id).text(parseFloat(total_units.toFixed(2)) + " " + display_opts.unit_str);
				$(display_opts.bill_id).text("$" + parseFloat(bill_amt.toFixed(2)));
			}
			// our starttime is the last hour boundary
			var starttime = time_ms - (time_ms % (60 * 60 * 1000));
			var endtime = time_ms;
			console.log("starttime: " + starttime + " endtime: " + endtime)
			var url_second_query = api_gethistory + "?uuid=" + uuid + "&starttime=" + starttime + "&endtime=" + endtime;
			$.getJSON(url_second_query, second_smap_query_success);
		}

		// gets the TOTAL of all the readings for the day
		function getDayTotal(uuid, total_except_today, display_opts) {
			function hours_db_query_success(data) {
				console.log("id: " + display_opts.unit_id + " hours db: " + JSON.stringify(data))
				var total_except_current_hour = total_except_today;
				$.each(data.data, function(i, val) {
					// val is the average reading for the hour, so
					// multiply by the number of seconds in an hour
					// to get the total of all the readings
					total_except_current_hour += val[1] * 60 * 60;
				});
				getHourTotal(uuid, total_except_current_hour, display_opts);
			}
			// get all the hours today except the current hour
			var hours_to_get = hour_num - 1;
			var url_hour_query = api_get_query_db + "?uuid=" + uuid + "&db=hours&length=" + hours_to_get;
			$.getJSON(url_hour_query, hours_db_query_success);
		}

		// gets the TOTAL of all the readings for the month
		function getMonthTotal(uuid, display_opts) {
			function days_db_query_success(data) {
				console.log("id: " + display_opts.unit_id + " days db: " + JSON.stringify(data))
				var total_except_today = 0;
				$.each(data.data, function(i, val) {
					// val is the average reading for the day, so
					// multiply by the number of seconds in a day 
					// to get the total of all the readings
					total_except_today += val[1] * 24 * 60 * 60;
				});
				getDayTotal(uuid, total_except_today, display_opts);
			}
			//get everything this month except today
			var days_to_get = date_num - 1;
			var url_days_query = api_get_query_db + "?uuid=" + uuid + "&db=days&length=" + days_to_get;
			$.getJSON(url_days_query, days_db_query_success);
		}
		
		getMonthTotal(power_uuid, {unit_multiplier: 1/3600000, price_per_unit: power_price, unit_str: "kWh", unit_id: "#power_mo_totl", bill_id: "#power_mo_bill"})
		getMonthTotal(water_uuid, {unit_multiplier: 0.001, price_per_unit: water_price, unit_str: "Liters", unit_id: "#water_mo_totl", bill_id: "#water_mo_bill"})

		/*function days_query_success(data){
			console.log("**** overview data: RAW" + JSON.stringify(data));
			var total_except_today = 0;
			$.each(data.data, function(i, val) {
				total_except_today += val[1]/1000;
			}


			function hour_query_success(data) {
				var total_except_curr_hour = total_except_today;
				$.each(data.data, function(i, val) {
					total_except_curr_hour += val[1]
				}
			}
						

			//till_now_amount = running_total
			//till_now_amount = till_now_amount/1000;
			//energy consumption of the day till the beginning of current hour in kWhr
			//or water
			//console.log('**** overview; DB till this hour: ' + till_now_amount);
			
			function get_cur_day(){
				//using smap
				console.log("**** overview; asking today's data");
				var seconds_total = 0;
				var url_seconds = '';
				start_time = parseInt(cur_time/60/60/1000)*60*60*1000;
				url_seconds = api_get_query_db+'?uuid='+uuid+"&length=1"+"&db=hours";
				console.log("**** overview; today's url: "+ url_seconds);
				console.log("**** overview; today start time: " + new Date(start_time));
				$.getJSON(url_seconds, function (data){
					console.log('**** overview; today data length: '+data.data.length);
					if (data.data.length<1){
						console.log("**** overview; No today live data for the hour");
						return 0;
					}
					console.log('**** overview; today data points RAW' + JSON.stringify(data));
					$.each(data.data, function(i,val){
						seconds_total += val[1];
					});
					seconds_total = seconds_total/data.data.length;
					console.log("**** overview; seconds_total"+ seconds_total);
					seconds_total = seconds_total/1000;
					console.log("**** overview; id: " + id +" hourly total: " + seconds_total);
					till_now_amount += seconds_total;
					//$(id).text("amount and " + till_now_unit);
					till_now_amount = multiplier*till_now_amount;
					$(id).text(parseFloat(till_now_amount.toFixed(2)) + till_now_unit);
					
				});
				//total of the hour by seconds					
				//unit of kWhr

			}
			//energy consumption of the hour till this moment

			get_cur_day();
			//till_now_amount = multiplier*till_now_amount;
			console.log('**** overview; till now with smap: '+ parseFloat(till_now_amount.toFixed(3))+ " -- multiplier: " + multiplier);
			console.log("**** overview: "+ "start time:  "+ new Date(start_time/1000) + "  current time: "+ new Date(cur_time)+ "  till now amount " + till_now_amount);

			
		}//end jsonSuccess


		// for power
		uuid = power_uuid;
		unit = 'W';
		till_now_unit = ' kWhr';
		multiplier = power_mul;
		id="#power_mo_totl";
		bill_id = "#power_mo_bill";
		start_time = cur_time - ((cur_time-7*60*60*1000) % (30*24*60*60*1000));
		//length = parseInt(((cur_time-7*60*60*1000)%(24*60*60*1000))/(60*60*1000));			
		

		
		// for water
		//uuid = water_uuid;
		//unit = 'cm^3/s';
		//till_now_unit = ' Liter';
		//multiplier = water_mul;	
		//id="#water_mo_totl";
		//bill_id = "#water_mo_bill";		
		//url = api_get_query_db + '?uuid=' + uuid + '&length=30'+'&db=days';
		//url= api_get_query_smap + '?uuid='+ uuid +'&starttime='+ start_time +'&window_size=' + window_size + '&window_unit=' + window_unit;
		//console.log("**** Stat URL: " + url);
		//$.getJSON(url,jsonSuccess);
				
		*/	

	});
	//end function()

}
//end of domloaded
