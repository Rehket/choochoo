import React from 'react';
import {makeStyles} from '@material-ui/core/styles';
import CssBaseline from '@material-ui/core/CssBaseline';
import Navigation from "./Navigation";


const useStyles = makeStyles(theme => ({
    root: {
        display: 'flex',
    },
    toolbar: theme.mixins.toolbar,
    content: {
        flexGrow: 1,
        padding: theme.spacing(1),  // paper has margin 1 so together we get 2 around all edges
    },
}));


export default function Layout(props) {

    const classes = useStyles();

    const {navigation, content, match, title} = props;

    return (
        <div className={classes.root}>
            <CssBaseline/>
            <Navigation content={navigation} match={match} title={title}/>
            <main className={classes.content}>
                <div className={classes.toolbar}/>
                {content}
            </main>
        </div>
    )
}