import * as slot_view from './slot_view.js';
import * as ko_view from './ko_view.js';
import * as address_view from './slot_address_view.js';
import * as area_view from './slot_area_view.js';
import * as group_view from './slot_group_view.js';
import * as integer_view from './slot_integer_view.js';
import * as select_view from './slot_select_view.js';

export class Slot_Controller {
    constructor(slot_model) {
        this.slot_model = slot_model;
        let controller = this;
        slot_model.on_value_updated = function(name) {
            controller.value_updated(name);
        };
        this.slot_view = new slot_view.Slot_View();
        this.ko_el = new select_view.Slot_Select_View();
        this.ko_views = [];
        for(var ko_i in this.slot_model.kos.values)
            this.ko_views.push(new ko_view.KO_View());
        this.initialize_view();
        this.set_fields_visibility();
    };
    get element() {
        return this.slot_view.element;
    };
    initialize_view() {
        let model = this.slot_model;
        if (model.fields===null) return;
        let controller = this;
        // step 1: display a control for the ko
        this.ko_el.label = "Operation mode";
        this.ko_el.on_change = function(value) {
            controller.ko_changed(value);
        };
        for(var ko_i in model.kos.values) {
            let ko_value = model.kos.values[ko_i];
            let ko_name = model.kos.names[ko_i];
            let ko_id = model.kos.ids[ko_i]
            this.ko_el.append_option(ko_value, ko_name, ko_id == model.values.KO);

            // generate the fields for each ko in the respective ko_view
            let ko_view = this.ko_views[ko_i];
            let ko_model = model.fields[ko_id];
            let names = model.names[ko_id];

            for(var f in model.fields[ko_id]) {
                let field = model.fields[ko_id][f];
                if (!field.disp) continue;
                let name = names[f]
                let current = model.get_value(name);
                var field_view = undefined;
                switch(field.field_type) {
                    case 'ADDRESS':
                        field_view = new address_view.Slot_Address_View();
                        field_view.label = field.description;
                        field_view.value = current;
                        break;
                    case 'INTEGER':
                        field_view = new integer_view.Slot_Integer_View();
                        field_view.label = field.description;
                        field_view.value = current;
                        break;
                    case 'LIST':
                        field_view = new select_view.Slot_Select_View();
                        field_view.label = field.description;
                        let list = model.lists[field.field_type_detail];
                        for(var o=0; o<list.values.length; o++) {
                            field_view.append_option(list.values[o], list.names[o], list.values[o]==current);
                        }
                        break;
                    default: 
                        console.log('unhandled', field);
                        field_view = undefined;
                };
                if (field_view!==undefined) {
                    let controller=this;
                    field_view.on_change = function (value) {
                        controller.field_changed(name, value);
                    };
                    //console.log(JSON.stringify(field_view));
                    ko_view.set_field(name, field_view);
                }
            }
        }
        this.slot_view.set_ko_element(this.ko_el);
        this.set_current_ko();
        return;
    };
    recurse_conditions(cond) {
        return true;
    };
    set_fields_visibility(){
        // let fields = this.slot_model.fields;
        // for(var field_name in fields) {
        //     var field_name = field_names[f];
        //     let field = fields[field_name];
        //     var can_display = true;
        //     if (field.cond!==undefined)
        //         can_display = this.recurse_conditions(field.cond);
        //     this.slot_view.set_visible(field_name, can_display);
        // }   
    };
    set_current_ko() {
        let ko_id = this.slot_model.get_value('KO');
        let i_ko = this.slot_model.kos.ids.indexOf(ko_id);
        this.slot_view.set_ko_view(this.ko_views[i_ko]);
    }
    ko_changed(value) {
        // value is a string !
        value = parseInt(value);
        let ko_values = this.slot_model.kos.values;
        let i_ko = ko_values.indexOf(value);
        let ko_ids = this.slot_model.kos.ids;
        this.slot_model.set_value('KO', ko_ids[i_ko]);
        let ko_view = this.ko_views[i_ko]
        this.slot_view.set_ko_view(ko_view);
    }
    field_changed(name, value) {
        if (this.slot_model.set_value(name, value)) 
            this.slot_view.set_field_valid(name);
        else  
            this.slot_view.set_field_invalid(name);
        this.set_fields_visibility();
    };
    value_updated(name) {
        var value = this.slot_model.get_value(name)
        this.slot_view.set_value(name, value);
        this.set_fields_visibility();
    }
}