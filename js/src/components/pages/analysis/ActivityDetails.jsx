import React, {useState} from 'react';
import {Text} from "../../elements";
import {Grid, InputLabel, MenuItem, Select} from "@material-ui/core";
import ActivityCard from "./ActivityCard";


export default function ActivityDetails(props) {

    const {params} = props;
    const [group, setGroup] = useState(params.latest_activity_group);
    const [datetime, setDatetime] = useState(params.latest_activity_time);
    const href = sprintf('jupyter/activity_details?local_time=%s&activity_group_name=%s', datetime, group);

    // force consistent date (will re-render)
    const datetimes = params.activities_by_group[group];
    if (! datetimes.includes(datetime)) {
        setDatetime(datetimes[datetimes.length - 1])
    }

    return (<ActivityCard header='Activity Details' displayWidth={4} href={href}>
        <Grid item xs={12}><Text>
            <p>Graphical details for the given activity.</p>
        </Text></Grid>
        <Grid item xs={3}>
            <InputLabel shrink>Group</InputLabel>
            <Select onChange={event => setGroup(event.target.value)} value={group}>
                {Object.keys(params.activities_by_group).map(group =>
                    <MenuItem value={group} key={group}>{group}</MenuItem>)}
            </Select>
        </Grid>
        <Grid item xs={5}>
            <InputLabel shrink>Time</InputLabel>
            <Select onChange={event => setDatetime(event.target.value)} value={datetime}>
                {params.activities_by_group[group].map(datetime =>
                    <MenuItem value={datetime} key={datetime}>{datetime}</MenuItem>)}
            </Select>
        </Grid>
    </ActivityCard>);
}
