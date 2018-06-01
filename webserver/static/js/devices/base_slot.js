export class Base_Slot {
    constructor(device, data) {
        console.log('Base_Slot::constructor');
        console.log(data);
        this.changed = false;
        this.device = device;
        this.number = device.slots.indexOf(this);
        this.data = data;
        this.options = data.options;
        // this needs to be done before fscking with the fields
        this.values = data.values;
        this.params = data.params;
        // create the ordered dataset
        this.fields = this.options.fields;
        if ((this.fields !== undefined) && (Array.isArray(this.fields))) {
            var ordered = [];
            var dict = {};
            for(var f=0; f<this.fields.length; f++) {
                var field = this.fields[f];
                if (ordered[field.order]===undefined)
                    ordered[field.order] = [];
                ordered[field.order].push(field);
                dict[field.name] = field;
                this.set_behavior(field);
            }
            var fields = {};
            fields.array = this.fields;
            fields.ordered = ordered;
            fields.dict = dict;
            this.fields = fields;
        } else
            console.log('WARNING: Expected data.options.fields to be an Array instance');
    };
    slot_elements(){
        console.log('Base_slot::slot_elements ', this.options);
        var sl = document.createElement('div');
        sl.classList.add('device-slot');
        // loops on each field and get it's main element back
        // each field is primed with it's own events
        for(var i=0; i<this.fields.ordered.length; i++){
            var layer = this.fields.ordered[i];
            if (layer===undefined)
                continue;
            for(var f=0; f<layer.length; f++) {
                var field = layer[f];
                if (field.elements!==undefined) {
                    var el = field.elements();
                    if (el!==undefined)
                        sl.appendChild(el);
                }
            }
        }
        // updates visibility of things
        this.show();
        return sl;
    };
    //------------------------------------------------------------------------
    //
    // Field helper functions
    //
    //
    get_value(fieldname) {
        return this.values[fieldname];
    };
    set_value(fieldname, value) {
        // updates the value for the field
        console.log('Base_Slot::set_value', fieldname, value);
        this.changed = true;
        this.values[fieldname] = value;
        // then, updates the visibility of things
        this.show();
    };
    show() {
        var array = this.fields.array;
        for(var i=0; i<array.length; i++) {
            var field = array[i];
            if (field.show!==undefined) 
                field.show();
        }
    }
    //------------------------------------------------------------------------
    //
    // Major javascript object hacking
    //
    //
    set_behavior(field) {
        let slot=this;
        // add behavior for every type
        field.recurse_conditions = function(cond) {
            // step 1: identify op
            var op = cond.op;
            switch (op) {
                // should not happen, obviously
                case undefined: 
                    console.log('no \'op\' specified');    
                    return true;
                case '==': 
                    if (cond.field===undefined) {
                        console.log('no \'field\' specified');
                        return true;
                    }
                    var f = slot.get_value(cond.field);
                    if (cond.value===undefined) {
                        console.log('no \'value\' specified');
                        return true;
                    }
                    return (f==cond.value);
                case 'in':
                    if (cond.field===undefined) {
                        console.log('no \'field\' specified');
                        return true;
                    }
                    var f = slot.get_value(cond.field);
                    if (cond.values===undefined) {
                        console.log('no \'values\' specified');
                        return true;
                    }
                    if (!Array.isArray(cond.values)) {
                        console.log('\'values\' should be an array', cond.values);
                        return true;
                    }
                    // scan the array, find if f is one of the values,
                    // returns true when that happens 
                    // (no need to scan the rest of the array)
                    for(var i=0; i<cond.values.length; i++) { 
                        if (f==cond.values[i])
                            return true;
                    }
                    // scanning the array unsuccessful...
                    return false;
                case 'and':
                    if ((cond.conditions === undefined) || (! Array.isArray(cond.conditions))) {
                        console.log('there should be an array of conditions in \'conditions\'', cond);
                        return true;
                    }
                    var result = true;
                    for(var ic=0; ic<cond.conditions.length; ic++)
                        result &= this.recurse_conditions(cond.conditions[ic]);
                    return result;
                default:
                    console.log('unknown operator \''+op+'\'', cond);
            }
            return true;
        };
        field.show_test = function(){
            // tests if the control should be displayed
            // if display is not defined, the thing should always be visible
            if (this.display===undefined)
                return true;
            // this gets more complicated ;)
            if (this.display.conditions!==undefined)
                return this.recurse_conditions(this.display.conditions);
            return false;
        };
        field.show = function(){
            // if no container, don't bother
            if (this.container===undefined) 
                return;
            this.container.hidden = !this.show_test();
        }
        // add behavior specific for all types
        switch (field.type) {
            case 'select': this.set_select_behavior(field); break;
        }
    };
    set_select_behavior(field) {
        let slot = this;
        //-------------------------------------------------------------------- 
        // add behavior to select element
        //
        // the elements generating function
        field.elements = function() {
            var ct = document.createElement('div');
            ct.classList.add('device-slot-line');
            this.container = ct;
            var lb = document.createElement('label');
            lb.classList.add('device-slot-label');
            lb.textContent = this.name;
            this.label = lb;
            var sl = document.createElement('select');
            sl.classList.add('device-slot-select');
            sl.addEventListener('change', ev => {
                var val = ev.target.value;
                slot.set_value(field.name, val);
            });
            // generate options
            var current = slot.get_value(this.name)
            for(var o=0; o<this.options.length; o++) {
                var opt = new Option(this.options[o], o, false, (o==current))
                sl.appendChild(opt);
            }
            this.select = sl;
            ct.appendChild(lb);
            ct.appendChild(sl);
            return ct;
        };
    };
}
