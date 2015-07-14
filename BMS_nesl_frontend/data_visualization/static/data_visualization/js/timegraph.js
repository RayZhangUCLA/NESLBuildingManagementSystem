document.addEventListener('DOMContentLoaded',domloaded,false);
function domloaded(){
	var pathArray = window.location.pathname.split('/');
	const api_gethistory = 'http://128.97.93.240:7000/data_visualization/dashboard/history_data?uuid=';
	const api_getcurrent = 'http://128.97.93.240:7000/data_visualization/dashboard/current_data?uuid=';
	const api_getPropotions = 'http://128.97.93.240:7000/data_visualization/dashboard/proportions?uuid=';
	const api_getEnergy = 'http://128.97.93.240:7000/data_visualization/dashboard/energy?uuid=';
	const api_get_query_smap = 'http://128.97.93.240:7000/data_visualization/dashboard/smap_query';
	const api_get_query_db = 'http://128.97.93.240:7000/data_visualization/dashboard/db_query';
	const water_uuid = '09bb4086-0335-26b2-1749-a489e7718337';
	const power_uuid = '6a6e1be3-2315-f849-f02c-adea4fe29099';
	var api_get_query=api_get_query_smap;
	var uuid = '';
	var url = '';
	var last_data;
	var last_timestamp;
	var cur_time=new Date().getTime();
	var start_time = cur_time - 60*1000;
	var graphname=null;
	var unit=null;
	var description=null;
	var window_size=5;
	var window_unit='second';
	var refresh_rate = 5000;
	var series = null;
	var selected_chart_id = "#time_series_chart"
	var data_name = $('#time_series_chart').attr('data-name');

	$(function () {
		Highcharts.setOptions({global: {useUTC: false}});
		
		if (data_name == 'power'){
			uuid = power_uuid;
			name = 'House power graph';
			description='Electricity Usage Graph (Average Power)';
			unit = 'W';

		}else if(data_name == 'water'){
			uuid = water_uuid;
			name = 'Water flow graph';
			description='Water Usage Graph';
			unit = 'cm^3/s';
		}
		//console.log(uuid);
		function jsonSuccess(data){
			console.log("returned data: " + data);
			//unit = data.unit;
			
			function setTimeSeriesHighchart(graphid, graphdata){
				console.log("graphdata: "+JSON.stringify(graphdata));
				console.log("updating highchart " + graphid);
				$(graphid).highcharts({
					chart: {
						type: 'spline',
						animation: Highcharts.svg, // don't animate in old IE
						marginRight: 10,
						backgroundColor: 'rgba(255,255,255,1)',
						events: {
							load: function () {
								// set up the updating of the chart each 10 second
								series = this.series[0];
								//console.log("this.series"+ JSON.stringify(this.series[0]));
								function get_current_val(selected_id, loop_refresh_rate) {
									console.log("got update for " + selected_id + " loop_refresh_rate " + loop_refresh_rate)
									if($(".btn_selected").attr("id") == selected_id) {
										$.get(api_getcurrent + uuid, function(data, s){
											last_data = series.data[series.data.length-1];
											console.log("series.data: "+ series.data);
											//console.log("last_data: " +JSON.stringify(last_data));
											last_timestamp=last_data['x'];
											data = $.parseJSON(data);
											console.log("data.data:  "+ JSON.stringify(data.data));
											if(data.data[0][0] > last_timestamp){
												series.addPoint(data.data[0], true, true);	
											}
										});
										//setTimeout(get_current_val, loop_refresh_rate, selected_id, loop_refresh_rate);
									}
									else {
										console.log("breaking out of refresh loop for" + selected_id)
									}
								}
								current_select_id = $(".btn_selected").attr("id");
								console.log("setting timeout for get_current_val refresh_rate: " + refresh_rate + " " + current_select_id)
								//setTimeout(get_current_val, refresh_rate, current_select_id, refresh_rate);
								setInterval(get_current_val, refresh_rate, current_select_id, refresh_rate);
							}
						}
					},

					title: {
						text: description,
					},
					xAxis: {
						type: 'datetime',
						tickPixelInterval: 150
					},
					yAxis: {
						title: {
							text: unit,
						},
						plotLines: [{
							value: 0,
							width: 1,
							color: '#808080'
						}],
					},
					tooltip: {
						formatter: function () {
							return Highcharts.numberFormat(this.y, 2) + " " + unit + "<br/>" + 
								Highcharts.dateFormat('%Y-%m-%d %H:%M:%S', this.x);
						}
					},
					legend: {
						enabled: false
					},
					exporting: {
						enabled: false
					},
					series: [{
						name: description,
						data:  graphdata.data,
						color: 'rgba(205,228,230,1)',
					}]
					//end series

				});
				//end highcharts
			}
			//end setTimeSeriesHighchart

			function setPieHighchart(piegraphid, piegraphdata){
				if (data_name == "water") {
					Highcharts.getOptions().plotOptions.pie.colors = (function() {
						var colors = [],
						    base = Highcharts.getOptions().colors[0],
						    i;
						for (i = 0; i < 7; i += 1) {
							colors.push(Highcharts.Color(base).brighten((i - 4) / 7).get());
						}
						return colors;
					}());
				}
				else if (data_name == "power") {
					Highcharts.getOptions().plotOptions.pie.showInLegend = false
				}
				var chart_title = "";
				if (data_name == "power") {
					chart_title = "Current Energy Usage By Device"
				}
				else if (data_name == "water") {
					chart_title = "Water Usage By Day"
				}
				$(piegraphid).highcharts({
					chart: {
						plotBackgroundColor: null,
						plotBorderWidth: null,
						plotShadow: false
					},
					title: {
						text: chart_title
					},
					tooltip: {
						pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
					},
					plotOptions: {
						pie: {
							allowPointSelect: true,
							cursor: 'pointer',
							dataLabels: {
								enabled: true,
								format: '<b>{point.name}</b>: {point.percentage:.1f} %',
								style: {
									color: (Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black'
								}
							}
						}
					},
					series: [{
						type: 'pie',
						name: data_name + ' Usage',
						/*data: [
							['Firefox',   45.0],
							['IE',       26.8],
							{
								name: 'Chrome',
								y: 12.8,
								sliced: true,
								selected: true
							},
							['Safari',    8.5],
							['Opera',     6.2],
							['Others',   0.7]
						]*/
						data: piegraphdata
					}]
				});

			}
			// end setPieHighchart_water

			setTimeSeriesHighchart(selected_chart_id,data);
			//amount of each day for 7 days
			if (data_name=='water'){
				function get_day(day_timestamp) { 
					date_obj = new Date(day_timestamp)
					day_num = date_obj.getDay();
					month_num = date_obj.getMonth() + 1;
					date_num = date_obj.getDate();
					
					day_str = null;
					switch (day_num) { 
						case 0:
							day_str = "Sunday";
							break;
						case 1:
							day_str = "Monday";
							break;
						case 2:
							day_str = "Tuesday";
							break;
						case 3:
							day_str = "Wednesday";
							break;
						case 4:
							day_str = "Thursday";
							break;
						case 5:
							day_str = "Friday";
							break;
						case 6:
							day_str = "Saturday";
							break;
						default:
							console.log("ERROR: invalid day")
					}
					return day_str + ", " + month_num + "/"  + date_num;
				}
				//setPieHighchart_water('#pie_chart', week_data);
				var water_uuid = ["09bb4086-0335-26b2-1749-a489e7718337", "Main water pipe for the whole building"];
				todays_date_obj = new Date()
				todays_date = todays_date_obj.getDate()
				todays_day = todays_date_obj.getDay()
				function waterPropSuccess(data) {
					console.log("water proportions data:" + JSON.stringify(data))
					water_readings = data.data
					water_props = [0, 0, 0, 0, 0, 0, 0]
					water_day_names = [null, null, null, null, null, null, null]
					for (i = 0; i < water_readings.length; i++) {
						ts = water_readings[i][0]
						/*if (ts < (cur_time - 7*24*60*60*1000)) {
							continue;
						}*/
						wr = water_readings[i][1]
						date_obj = new Date(ts)
						date_num = date_obj.getDate()
						day_num = date_obj.getDay()
						if (day_num == todays_day && date_num != todays_date) {
							continue;
						}
						water_day_names[day_num] = get_day(ts)  
						water_props[day_num] += wr 
					}
					water_highchart_data = []
					for (i = 0; i < water_props.length; i++) {
						water_highchart_data[i] = [water_day_names[i], water_props[i]]
					}
					setPieHighchart("#pie_chart", water_highchart_data)
				}
				// build the url and query the data
				water_prop_url = api_get_query_db + "?uuid=" + water_uuid[0] + "&length=168&db=hours" 
				console.log("water proportions url: " + water_prop_url)
				$.getJSON(water_prop_url, waterPropSuccess)
				
			}else if (data_name =='power'){
				power_uuids = [
					["388c5f99-ea11-1115-04aa-d0e44d77d50a", "Sony KDL-52XBR3 TV"],
					["67d49688-5d3a-2a60-f046-6f533c40e297", "SQ Blaster+"],
					["a66a2e8f-5d04-ddcb-fb2e-c30c80ed7f14", "Onkyo TX-SR805 & LG BD630 DVD"],
					["269d11d5-8f52-e520-ca49-9e0b5cfa20e3", "Apple TV 2"],
					["80b263bc-5f51-54f5-3809-076808967966", "DISH Hopper"],
					["5025031a-292c-6fad-f8e0-5cc4c19139f0", "Foscam FI8918W"],
					["2f6efc33-d3a9-bcff-f551-4375c3bd9130", "Netgear Switch GS108"],
					["7e1f5f6f-3a79-2e2a-0c99-c2e90e75e75d", "PowerStrip: Headphone-Remote-Wii-Airport-KEF Tx"],
					["7853f00d-1912-8add-df84-c29345d3aa47", "RS_Device1"],
					["418c7610-f3c9-176e-51c0-7ff9346b5065", "RS_Device2"],
					["a2135f3f-1955-8d7b-f3d6-80ff99493be3", "RS_Device3"],
					["5afe53db-6e19-782e-84d4-0f15e105a0d0", "RS_Device4"],
					["8b7b2644-6123-e5b5-e270-bdf830999241", "RS_Device5"],
					["8b485785-a073-c439-1022-8ef5bfdc024e", "RS_Device6"],
					["64ad492e-2837-085d-e0ac-78ea92328562", "RS_Device7"],
					["4f0d98bf-a826-15e7-9e40-378952962214", "RS_Device8"],
					//["b55ca829-5846-3a1d-6d88-ef9b37e9a870", "TED5000-100BED (Subpanel)"],
					["7c4b9261-a4cd-063e-ab27-1a14164a2aaa", "TED5000-100D4F (Oven)"],
					["0bb80e04-7b37-3ddf-a126-7bd74030374f", "TED5000-100BEE (Pool)"],
					["2735aede-e684-f11a-2e46-5bd150bec4c9", "Rec Room Outlet"],
					["6b58ffed-7dc9-bb53-0289-72a033e3f8ad", "Rec Room Outlet"],
					["0b795679-80a7-d05d-99b8-068200b9e01e", "Spa Tub"],
					["2c6ac4b8-0ba3-4f00-58c4-dbd5262e57b0", "Bath GFI"],
					["804be622-d4d9-3341-4d3a-fc066ce83430", "Bath GFI (master bath- washlet)"],
					["041cba9b-fcc4-56e5-c363-2b9eec97f048", "Rec Room Fan & Lights"],
					["b6c7c4d5-82bd-6ebe-2d54-0d0abbc05c2c", "Rec Room Outlets"],
					["3f3e542e-da41-9cd4-fe07-09bcb068ffc2", "Rec Room TV Outlets"],
					//["e7fe87df-677d-4514-ebd1-dcdbd9a708c8", "eGauge_MainPanel_1/Ptot_apparent"],
					//["d2b8e51f-5bb7-92bd-f336-bc57b42afc8b", "eGauge_MainPanel_1/Ptot_apparent"],
					["43cfe35f-3650-fa01-9d1f-75d8825c3b0b", "Megha-light-computer-lamps-bath"],
					["a4fdbc88-e13d-1d47-d5c6-087e2b93fafd", "Red - Megha fan/light"],
					["d8bf0121-fed2-c018-ad86-c359923c989c", "AC"],
					["ee60f57d-e41a-844c-8cbb-683dda864b24", "Black-Megha bathroom-garage exhaust"],
					["42d726ae-0409-8544-398f-7b01969f8c63", "Plugs"],
					["83c37b8b-8fb9-f63c-6a81-5a8dfc8ff90d", "Garage"],
					["7d7b8f8e-0dcf-5f87-ed08-88d39a8525ce", "Wall AC in Rec Room"],
					/*["eb86f4ac-2bd2-88fd-0203-e19b443c690f", "Main Panel 2 Power Total Real"],
					["d63584d9-8926-d3ce-2bc8-e45df66e52fa", "Main Panel 2 Power Total Real"],
					["6a6e1be3-2315-f849-f02c-adea4fe29099", "Main Panel 2 Power House Real"]*/]
				uuid_str = ""
				for (i = 0; i < power_uuids.length - 1; i++) {
					uuid_str += power_uuids[i][0] + ","
					
				}
				uuid_str += power_uuids[power_uuids.length - 1][0]

				prop_end_time = $.now()
				prop_start_time = prop_end_time - 10000;
				proportions_url = 'http://128.97.93.240:7000/data_visualization/dashboard/proportions?uuids=' + uuid_str + "&starttime="+ prop_start_time + "&endtime=" + prop_end_time;
				function powerPropSuccess(data) {
					console.log("prop_success: " + data)
					power_props = []
					for (i = 0; i < data.length; i++) {
						if (data[i] > 0) {
							power_props.push([power_uuids[i][1], data[i]])
						}
					}
					
					setPieHighchart("#pie_chart", power_props)
					
				}
				console.log("proportions url: " + proportions_url)
				$.getJSON(proportions_url, powerPropSuccess)
				setPieHighchart("#pie_chart", null )
				
			}
				
		}
		//end jsonSuccess
		//url = api_gethistory+uuid+'&starttime='+start_time;
		
		url= api_get_query + '?uuid='+ uuid +'&starttime='+ start_time +'&window_size=' + window_size + '&window_unit=' + window_unit;
		console.log("url = " + url);
		$.getJSON(url,jsonSuccess);

		// Registering clicks
		$('#minute').click(function(){
			$('.time_series_chart_selected').removeClass('time_series_chart_selected');
			$('#time_series_chart').addClass('time_series_chart_selected');
			$('.btn_selected').removeClass('btn_selected');
			$(this).addClass('btn_selected');
			starttime = cur_time-60*1000;
			api_get_query = api_get_query_smap;
			url= api_get_query + '?uuid='+ uuid +'&starttime=' + starttime + '&window_size=5&window_unit=second';
			selected_chart_id = "#time_series_chart"
			$.getJSON(url,jsonSuccess);
			refresh_rate = 5*1000;
		});
		$('#hour').click(function(){
			$('.time_series_chart_selected').removeClass('time_series_chart_selected');
			$('#time_series_chart_hour').addClass('time_series_chart_selected');
			$('.btn_selected').removeClass('btn_selected');
			$(this).addClass('btn_selected');
			starttime = cur_time-60*60*1000;
			api_get_query = api_get_query_smap;
			url= api_get_query + '?uuid='+ uuid +'&starttime=' + starttime + '&window_size=60&window_unit=second';
			selected_chart_id = "#time_series_chart_hour"
			$.getJSON(url,jsonSuccess);
			refresh_rate = 30*1000;
		});
		$('#day').click(function(){
			$('.time_series_chart_selected').removeClass('time_series_chart_selected');
			$('#time_series_chart_day').addClass('time_series_chart_selected');
			$('.btn_selected').removeClass('btn_selected');
			$(this).addClass('btn_selected');
			starttime = cur_time-60*60*24*1000;
			window_unit = 'hour';
			window_size = 1;
			api_get_query = api_get_query_db;
			url= api_get_query + '?uuid='+ uuid +'&length=24&db=hours';
			selected_chart_id = "#time_series_chart_day"
			$.getJSON(url,jsonSuccess);
			refresh_rate = 60*60*1000;
		});
		$('#week').click(function(){
			$('.time_series_chart_selected').removeClass('time_series_chart_selected');
			$('#time_series_chart_week').addClass('time_series_chart_selected');
			$('.btn_selected').removeClass('btn_selected');
			$(this).addClass('btn_selected');
			starttime = cur_time-7*60*60*24*1000;
			window_unit='hour';
			window_size = 1;
			api_get_query = api_get_query_db;
			url= api_get_query + '?uuid='+ uuid + '&length=168'+'&db=hours';
			selected_chart_id = "#time_series_chart_week" 
			$.getJSON(url,jsonSuccess);
			refresh_rate = 60*60*1000;
		});
		$('#month').click(function(){
			console.log("click registered for month")
			$('.time_series_chart_selected').removeClass('time_series_chart_selected');
			$('#time_series_chart_month').addClass('time_series_chart_selected');
			$('.btn_selected').removeClass('btn_selected');
			$(this).addClass('btn_selected');
			window_unit='day';
			window_size=1;
			api_get_query = api_get_query_db;
			url= api_get_query + '?uuid=' + uuid +'&length=30'+'&db=days';
			selected_chart_id = "#time_series_chart_month"
			$.getJSON(url,jsonSuccess);
			refresh_rate = 24*60*60*100;
		});

		$('#year').click(function(){
			$('.time_series_chart_selected').removeClass('time_series_chart_selected');
			$('#time_series_chart_year').addClass('time_series_chart_selected');
			$('.btn_selected').removeClass('btn_selected');
			$(this).addClass('btn_selected');
			window_unit = 'day';
			window_size = 1;
			api_get_query=api_get_query_db;
			url= api_get_query + '?uuid=' + uuid +'&length=365&db=days';
			selected_chart_id = "#time_series_chart_year"
			$.getJSON(url,jsonSuccess);
			refresh_rate = 24*60*60*1000;
		});
		//end of click functions

	});
	//end (function()	)

//end domeloaded
}


