import React from 'react';
import {BrowserRouter, Route, Switch} from 'react-router-dom';
import Diary from './diary/Diary';


export default function Routes() {
    return (
        <BrowserRouter>
            <Switch>
                <Route path='/:date' component={Diary}/>
                <Route component={Diary}/>
            </Switch>
        </BrowserRouter>
    );
}
