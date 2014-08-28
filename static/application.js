$( document ).ready(function() {
    var map = L.map('big-map', {
        center: [50.05, 19.95],
        zoom: 12,
    });

    L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
        maxZoom: 18
    }).addTo(map);

    var current_markercluster;
    var current_heatmap;

    var reload_points = function(){
        if(current_markercluster){
            map.removeLayer(current_markercluster);
            current_markercluster = null;
        }
        if(current_heatmap){
            map.removeLayer(current_heatmap);
            current_heatmap = null;
        }
        var markers = new L.MarkerClusterGroup({ maxClusterRadius: 15 });
        var heatmap = new HeatmapOverlay({
            latField: 'lat',
            lngField: 'lon',
            valueField: 'rssi',
            scaleRadius: true,
            useLocalExtrema: true,
            radius: 0.001,
            maxOpacity: .6 });
        var heatmap_data = { max: 100, data: new Array() };

        var current_bounds = map.getBounds();

        var filter_ssid = "";

        $.ajax({
            url: "/api/get_points",
            data: {
                boundN: current_bounds.getNorth(),
                boundE: current_bounds.getEast(),
                boundW: current_bounds.getWest(),
                boundS: current_bounds.getSouth(),
                filter_ssid: filter_ssid,
            },
            success: function( data ) {
                console.log('Reloaded, loaded points: ' + data.points.length);
                for(point in data.points){
                    var current_point = data.points[point];

                    var marker = new L.marker([current_point.lat, current_point.lon], {title: current_point.ssid});
                    var desc = "MAC: " + current_point.mac;
                    desc += "<br /> SSID: <b>" + current_point.ssid + "</b>";
                    desc += "<br />";
                    for(tag in current_point.tags){
                        desc += "<br />" + current_point.tags[tag];
                    }
                    marker.bindPopup(desc);

                    markers.addLayer(marker);

                    heatmap_data.data.push({
                        lat: current_point.lat,
                        lon: current_point.lon,
                        rssi: current_point.rssi + 100,
                    });
                }

                current_heatmap = heatmap;
                map.addLayer(heatmap);
                heatmap.setData(heatmap_data);

                current_markercluster = markers;
                map.addLayer(markers);
            }
        });
    }

    reload_points();

    map.on('moveend', function(dist){
        reload_points();
    });
});

