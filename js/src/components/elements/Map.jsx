import React, {useEffect, useState} from 'react';
import {Circle, LayerGroup, MapContainer, Polyline, TileLayer} from "react-leaflet";
import {Grid} from "@material-ui/core";
import {makeStyles} from "@material-ui/styles";
import {last} from '../../common/functions';
import {Loading} from "../../common/elements";
import log from "loglevel";


const useStyles = makeStyles(theme => ({
    map: {
        height: 300,
    },
    map_container: {
        height: '100%',
    }
}));


// export default function Map(props) {
//
//     const classes = useStyles();
//
//     const {json} = props;
//
//     return (
//         <Grid item xs={12} className={classes.map}>
//             <MapContainer center={[51.505, -0.09]} zoom={13} scrollWheelZoom={false}
//                           className={classes.map_container}>
//                 <TileLayer attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
//                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
//                 <Marker position={[51.505, -0.09]}>
//                     <Popup>A pretty CSS3 popup. <br /> Easily customizable.</Popup>
//                 </Marker>
//             </MapContainer>
//         </Grid>);
// }


export default function Map(props) {

    const {json} = props;
    const [data, setData] = useState(null);

    useEffect(() => {
        fetch('/api/route/' + json.db[0] + '/' + encodeURIComponent(json.db[1]))
            .then(response => response.json())
            .then(setData);
    }, [json.db]);

    return (data === null ? <Loading/> : <ActivityMap data={data}/>)
}


function ActivityMap(props) {

    const classes = useStyles();

    const {data} = props;

    const latlon = data['latlon'];
    const lats = latlon.map(latlon => latlon[0]).sort();
    const lons = latlon.map(latlon => latlon[1]).sort();
    const bounds = [[lats[0], last(lons)], [last(lats), lons[0]]];

    // log.debug(`lats ${lats}`);
    // log.debug(`lons ${lons}`);
    // log.debug(`Bounds ${bounds}`);

    const red = {fillColor: 'red', color: 'red', fillOpacity: 1};
    const green = {fillColor: 'green', color: 'green', fillOpacity: 1};

    return (
        <Grid item xs={12} className={classes.map}>
            <MapContainer bounds={bounds} scrollWheelZoom={false}
                          className={classes.map_container}>
                <TileLayer attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
                           url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
                {activity_routes(data)}
                <LayerGroup>
                    <Circle center={last(latlon)} radius={100} pathOptions={red} key={1}/>
                    <Circle center={latlon[0]} radius={70} pathOptions={green} key={2}/>
                </LayerGroup>
            </MapContainer>
        </Grid>);
}


function activity_routes(data) {
    const latlon = data['latlon'];
    const routes = [<ActivityRoute route={latlon} key={-1}/>]
    if ('sectors' in data) {
        return [...routes,
            ...data['sectors'].map((sector, i) =>
                <ActivityRoute route={sector['latlon']}
                               color={sector['type'] === 1 ? 'cyan' : 'black'}
                               key={i}/>)];
    } else {
        return routes;
    }
}


function ActivityRoute(props) {
    const [opacity, setOpacity] = useState(1.0);
    const {route, color='grey', weight=3} = props;
    return <Polyline pathOptions={{color: color, weight: weight, opacity: opacity}} positions={route}
                     eventHandlers={{mouseover: e => setOpacity(0.5),
                                     mouseout: e => setOpacity(1.0)}}/>;
}
