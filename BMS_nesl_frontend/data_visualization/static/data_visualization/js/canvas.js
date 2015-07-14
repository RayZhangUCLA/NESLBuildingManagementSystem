
document.addEventListener('DOMContentLoaded',domloaded,false);
function domloaded(){
	
	//Heat map function
	$(function () {
		var url="http://128.97.93.240:7000/data_visualization/dashboard/layout_data";
		var power_stream = [];
		var water_stream = [];

		//click and replace heatmaps for water and energy
		$('#P').click(function(){
			$('.heatmap_selected').removeClass('heatmap_selected');
			$('#container').addClass('heatmap_selected');
			$('.btn_selected').removeClass('btn_selected');
			$(this).addClass('btn_selected');
			
		});
		$('#W').click(function(){
			$('.heatmap_selected').removeClass('heatmap_selected');
			$('#watermap').addClass('heatmap_selected');
			$('.btn_selected').removeClass('btn_selected');
			$(this).addClass('btn_selected');

		});

		function json_success(data){
			power_stream = [{x: 0, y: 0, value: 0, name: null, color: 'rgba(0,0,0,0)'}, {x: 75, y: 75, value: 0, name: null, color: 'rgba(0,0,0,0)'}];
			water_stream = [{x: 0, y: 0, value: 0, name: null, color: 'rgba(0,0,0,0)'}, {x: 75, y: 75, value: 0, name: null, color: 'rgba(0,0,0,0)'}];
			$.each(data, function(i,val){
				if (val['tab_type'] == 'power' && val['heat_map_enable']) {
				//if (val['channel_units'] == 'Watts (W)') {
					console.log("val:" + JSON.stringify(val));
					power_stream.push({x: val['x_coord'], y: val['y_coord'], value: val['value'], name: val['description']});
				}
				if(val['tab_type'] == 'water' && val['heat_map_enable']){
					water_stream.push({x: val['x_coord'], y: val['y_coord'], value: val['value'], name: val['description']});
				}
			});

			//console.log("power_stream:" + power_stream);

			function setHighchart(graph_id, graph_data){
				$(graph_id).highcharts({
						
						chart: {
							type: 'heatmap',
							marginTop: 40,
							marginBottom: 40,
							backgroundColor:'rgba(255, 255, 255, 0.1)',
						},
			
			
						title: {
							text: null
						},
			
						
						xAxis: {
							//categories: ['Alexander', 'Marie', 'Maximilian', 'Sophia', 'Lukas', 'Maria', 'Leon', 'Anna', 'Tim', 'Laura']
							title: null,
							lineWidth: 0,
							minTickInterval: 1,
							minorGridLineWidth: 1,
							minorTickLength: 0,
							tickLength: 0,
							lineColor: 'transparent',
							//change gridLineWidth to 1 to see it
							gridLineWidth: 0,
							tickPixelInterval: 1,
							labels: {
								enabled: false
							}
						},
			
						yAxis: {
							//categories: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
							minTickInterval: 1,
							title: null,
							//change gridlinewidth to 1 to see it.
							gridLineWidth: 0,
							minorGridLineWidth: 1,
							lineColor:'black',
							tickPixelInterval: 1,
							labels: {
								enabled: false
							}
						},
			
						colorAxis: {
							min: 0,
							minColor: 'rgba(0,255,0,0.4)',
							
							maxColor: Highcharts.getOptions().colors[5],
						},
			
						legend: {
							align: 'right',
							layout: 'vertical',
							margin: 0,
							verticalAlign: 'top',
							y: 25,
							symbolHeight: 320
						},
			
						tooltip: {
							useHTML: true,
							hideDelay: 1000,
							formatter: function () {
								if(this.point.x>0 && this.point.x<75){
								if(graph_id == '#container'){
									var x_coord = '<b> x: \t' + this.point.x +'</b>';
									var y_coord = '<b> y: \t' + this.point.y +'</b>';
									return '<b> Power Consumption:     \t ' + this.point.value + " W <br/>" + this.point.name +'<br/></b>' + x_coord + y_coord;
								}
								if(graph_id == '#watermap'){
									var x_coord = '<b> x: \t' + this.point.x +'</b>';
									var y_coord = '<b> y: \t' + this.point.y +'</b>';
									return '<b> Water Consumption:     \t ' + this.point.value + " cm^3/s <br/>" + this.point.name +'<br/></b>' + x_coord + y_coord;
								}
								//return '<b>' + this.series.xAxis.categories[this.point.x] + '</b> Energy:  <br><b>' +
								//    this.point.value + '</b> Features: <br><b>' + this.series.yAxis.categories[this.point.y] + '</b>';
								}else return false;
							}
						},
			
						series: [{
							name: 'Energy Consumption',
							borderWidth: 0,
							data: graph_data,
							//data: [[0,0,0],[0,1,19],[0,2,8],[0,3,24],[0,4,67],[1,0,92],[1,1,58],[1,2,78],[1,3,117],[1,4,48],[2,0,35],[2,1,15],[2,2,123],[2,3,64],[2,4,52],[3,0,72],[3,1,132],[3,2,114],[3,3,19],[3,4,16],[4,0,38],[4,1,5],[4,2,8],[4,3,117],[4,4,115],[5,0,88],[5,1,32],[5,2,12],[5,3,6],[5,4,120],[6,0,13],[6,1,44],[6,2,88],[6,3,98],[6,4,96],[7,0,31],[7,1,1],[7,2,82],[7,3,32],[7,4,30],[8,0,85],[8,1,97],[8,2,123],[8,3,64],[8,4,84],[9,0,47],[9,1,114],[9,2,31],[9,3,48],[9,4,91],[10,10,0]],
							//data: [[0,0,0],[75,75,0],[2,75,10],[3,75,5],[4,75,10],[5,75,5],[6,75,10],[7,75,5],[8,75,10],[9,75,5],[10,75,10],[30,75,10],[32,75,10],[2,74,10],[3,73,5],[4,72,10],[5,71,5],[6,70,10],[7,69,5],[8,68,10],[9,67,5],[10,66,10]],
							dataLabels: {
								enabled: false,
								color: 'rgba(255, 255, 255, 0.1)',
								
								style: {
									textShadow: 'none'
								}
			
							}
			
						}]
			
					})}

		setHighchart('#container', power_stream);
		setHighchart('#watermap', water_stream);
		setTimeout(function(){
			$.getJSON(url,json_success);
			}, 5000);
		
		//setTimeout(function() {alert("Goodbye")}, 5000);
		}
		//description + tab_type + value + channel_units

		$.getJSON(url,json_success);
		//setTimeout(function() {alert("Hello")}, 3000);
		});
	}


