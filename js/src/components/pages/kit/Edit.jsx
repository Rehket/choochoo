import React, {useEffect, useState} from 'react';
import {Break, ColumnCard, ColumnCardBase, ColumnList, Layout, Loading, MainMenu, Text} from "../../elements";
import {
    Box,
    Button,
    Collapse,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    Grid,
    TextField,
    Typography,
    useMediaQuery,
    useTheme
} from "@material-ui/core";
import {makeStyles} from "@material-ui/core/styles";
import {Autocomplete} from "@material-ui/lab";
import {ExpandLess, ExpandMore} from "@material-ui/icons";


const useStyles = makeStyles(theme => ({
    right: {
        textAlign: 'right',
    },
    center: {
        textAlign: 'center',
    },
    left: {
        textAlign: 'left',
    },
    h3: {
        marginTop: theme.spacing(2),
    },
}));


function ConfirmedWriteButton(props) {

    const {children, href, data={}, label, xs = 12, update=null, disabled=false} = props;
    const classes = useStyles();
    const [openConfirm, setOpenConfirm] = React.useState(false);
    const [openWait, setOpenWait] = React.useState(false);
    const theme = useTheme();
    const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

    function handleClickOpen() {
        setOpenConfirm(true);
    }

    function handleWrite() {
        setOpenWait(false);
        if (update !== null) update();
    }

    function handleCancel() {
        setOpenConfirm(false);
    }

    function handleOk() {
        handleCancel();
        setOpenWait(true);
        fetch(href,
            {method: 'put',
                  headers: {'Accept': 'application/json', 'Content-Type': 'application/json'},
                  body: JSON.stringify(data)})
            .then(handleWrite)
            .catch(handleWrite);
    }

    return (
        <Grid item xs={xs} className={classes.right}>
            <Button variant="outlined" onClick={handleClickOpen} disabled={disabled}>{label}</Button>
            <Dialog fullScreen={fullScreen} open={openConfirm} onClose={handleCancel}>
                <DialogTitle>{'Confirm modification?'}</DialogTitle>
                <DialogContent>
                    <DialogContentText>{children}</DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button autoFocus onClick={handleCancel}>Cancel</Button>
                    <Button onClick={handleOk} autoFocus>OK</Button>
                </DialogActions>
            </Dialog>
            <Dialog fullScreen={fullScreen} open={openWait}>
                <DialogTitle>{'Please wait'}</DialogTitle>
                <DialogContent>
                    <DialogContentText>Saving data.</DialogContentText>
                </DialogContent>
            </Dialog>
        </Grid>
    );
}


function ModelShow(props) {

    const {item, model, component, update} = props;
    const classes = useStyles();
    const [newModel, setNewModel] = useState(model.name);
    const disabled = newModel === '';

    return (<>
        <Grid item xs={12} className={classes.h3}>
            <Typography variant='h3'>{component.name} / {model.added}</Typography>
        </Grid>
        <Grid item xs={9}>
            <Autocomplete options={component.models.map(model => model.name)} freeSolo value={newModel}
                          onInputChange={(event, value) => setNewModel(value)}
                          renderInput={params => <TextField {...params} label='Model' variant='outlined'/>}/>
        </Grid>
        <ConfirmedWriteButton xs={3} label='Replace' disabled={disabled}
                              href='/api/kit/replace-model' update={update}
                              data={{'item': item.name, 'component': component.name, 'model': newModel}}>
            Adding a new model will replace the current value from today's date.
        </ConfirmedWriteButton>
    </>);
}


function AddComponent(props) {

    const {item, update, allComponents} = props;
    const [component, setComponent] = useState('');
    const [model, setModel] = useState('');
    const existing = item.components.map(component => component.name);
    const components = Object.keys(allComponents).filter(component => ! existing.includes(component));
    const models = components.includes(component) ? allComponents[component].map(model => model.name) : [];
    const disabled = component === '' || model === '';

    return (<>
        <Grid item xs={12}>
            <Box mt={3}><Text>To add a completely new component and model:</Text></Box>
        </Grid>
        <Grid item xs={9}>
            <Autocomplete options={components} label='Component' freeSolo value={component}
                          onInputChange={(event, value) => setComponent(value)}
                          renderInput={params => <TextField {...params} label='Component' variant='outlined'/>}/>
        </Grid><Break/>
        <Grid item xs={9}>
            <Autocomplete options={models} label='Model' freeSolo value={model}
                          onInputChange={(event, value) => setModel(value)}
                          renderInput={params => <TextField {...params} label='Model' variant='outlined'/>}/>
        </Grid>
        <ConfirmedWriteButton xs={3} label='Add' disabled={disabled}
                              href='/api/kit/add-component' update={update}
                              data={{'item': item.name, 'component': component, 'model': model}}>
            Adding a new component and model will extend this item from today's date.
        </ConfirmedWriteButton>
    </>);
}


function ItemShow(props) {
    const {item, group, update, allComponents} = props;
    let model_dbs = item.models.map(model => model.db);
    return (<ColumnCard>
        <Grid item xs={9}>
            <Typography variant='h2'>{item.name} / {group.name} / {item.added}</Typography>
        </Grid>
        <ConfirmedWriteButton xs={3} label='Retire'
                              href='/api/kit/retire-item' update={update} data={{'item': item.name}}>
            Retiring this item will remove it and all components from today's date.
        </ConfirmedWriteButton>
        {item.components.map(
            component => component.models.filter(model => model_dbs.includes(model.db)).map(
                model => <ModelShow item={item} model={model} component={component}
                                    update={update} key={model.db}/>)).flat()}
        <AddComponent item={item} update={update} allComponents={allComponents}/>
    </ColumnCard>);
}


function Introduction(props) {

    const {groups, update} = props;
    const [help, setHelp] = useState(groups.length === 0);

    function onClick() {
        setHelp(!help);
    }

    const header = (<Typography variant='h2'>
        Introduction
        <Button onClick={onClick}>{help ? <ExpandLess/> : <ExpandMore/>}</Button>
    </Typography>);

    return (<ColumnCardBase header={header}><Collapse in={help} timeout="auto" unmountOnExit>
        <Text>
            <p>'Kit' is the equipment you use when training.
                For me, for example, this tracks my bikes and their components.</p>
            <p>Everything is divided into four levels:
                <ul>
                    <li>At the top are 'groups'. A group might be 'bike' or 'shoes', for example.</li>
                    <li>Groups contain 'items', An item might be a particular bike.</li>
                    <li>Items are made from 'components'. These are generic things like 'wheel' or 'chain',</li>
                    <li>Finally, we have 'models' which are particular components.
                        For example, a particular make of wheel, or a model of chain.
                    </li>
                </ul>
            </p>
            <p>As your equipment changes over time you can change the current model,
                replacing what was used with a new model.</p>
            <p>You should also specify the item (eg the bike) when uploading data, so that the system can track when
                kit is being used.</p>
            <p>Using the options in the menu you can then see what kit you had at any particular time (a snapshot)
                and how long particular models lasted (statistics).
                So for me, tracking my bikes, I can see which models of chain last best, for example.</p>
        </Text>

    </Collapse>
        <AddGroup groups={groups} update={update}/>
    </ColumnCardBase>);
}


function AddGroup(props) {

    const {groups, update} = props;
    const [group, setGroup] = useState('');
    const [item, setItem] = useState('');
    const existingGroups = groups.map(component => component.name);
    const existingItems = groups.filter(g => g.name === group).map(g => g.items.map(i => i.name)).flat();
    const disabled = group === '' || item === '' || existingItems.includes(item);

    return (<>
        <Grid item xs={12}>
            <Box mt={3}><Text>To add a completely new group or item:</Text></Box>
        </Grid>
        <Grid item xs={9}>
            <Autocomplete options={existingGroups} label='Group' freeSolo value={group}
                          onInputChange={(event, value) => setGroup(value)}
                          renderInput={params => <TextField {...params} label='Group' variant='outlined'/>}/>
        </Grid><Break/>
        <Grid item xs={9}>
            <Autocomplete options={[]} label='Item' freeSolo value={item}
                          onInputChange={(event, value) => setItem(value)}
                          renderInput={params => <TextField {...params} label='Item' variant='outlined'/>}/>
        </Grid>
        <ConfirmedWriteButton xs={3} label='Add' disabled={disabled}
                              href='/api/kit/add-group' update={update}
                              data={{'group': group, 'item': item}}>
            Adding a new group or item will help you track more kit use.
        </ConfirmedWriteButton>
    </>);
}


function Columns(props) {

    const {groups, update} = props;

    if (groups === null) {
        return <Loading/>;  // undefined initial data
    } else {
        const allComponents = {};
        groups.forEach(group => group.items.forEach(item => item.components.forEach(
            component => allComponents[component.name] = component.models)));
        return (<ColumnList>
            <Introduction groups={groups} update={update}/>
            {groups.map(
                group => group.items.map(
                    item => <ItemShow item={item} group={group} update={update} key={item.db}
                                      allComponents={allComponents}/>)).flat()}
        </ColumnList>);
    }
}


export default function Edit(props) {

    const {match} = props;
    const [json, setJson] = useState(null);
    const [edits, setEdits] = useState(0);

    function update() {
        setEdits(edits + 1);
    }

    useEffect(() => {
        setJson(null);
        fetch('/api/kit/edit')
            .then(response => response.json())
            .then(json => setJson(json));
    }, [edits]);

    return (
        <Layout navigation={<MainMenu kit/>}
                content={<Columns groups={json} update={update}/>}
                match={match} title='Edit Kit'/>
    );
}
