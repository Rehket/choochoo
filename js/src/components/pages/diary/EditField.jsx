import React from 'react';
import TreeItem from "@material-ui/lab/TreeItem";
import TextField from "@material-ui/core/TextField";



export default function EditField(props) {

    const {json, writer} = props;
    const [value, setValue] = React.useState(json.value === null ? '' : json.value);

    function handleChange(event) {
        setValue(event.target.value);
        let data = {};
        data[json.label] = event.target.value;
        writer.postMessage(data);
    }

    return <TreeItem key={props.json.id} nodeId={props.json.id} label={
        <TextField label={props.json.label} value={value} onChange={handleChange}
                   fullWidth variant="filled"/>
    }/>;
}