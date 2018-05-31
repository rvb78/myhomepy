import * as base from './base_device.js';

let dev_types = {
    2 : {
        nb_slots : 2,
        references : {
            'BRAND_UNDEFINED' : {
                0 : '<unknown>'
            },
            'BRAND_BTICINO' : {
                icon: 'BTicino',
                3 : 'Axolute H4652/2'
            },
            'BRAND_LEGRAND' : {
                icon: 'Legrand',
                4 : 'Céliane 067552'
            }
        }
    }
}

class Slot_4652 extends base.Base_Slot {
    constructor (device, data) {
        super(device, data);
    };
}

export class Device_4652 extends base.Base_Device {
    constructor(data, config_page) {
        super(data, config_page);
        this.dev_types = dev_types;
        this.set_device_reference();

        if (this.model_id == 2) {
            this.slots = new Array(2);
        }
        for(var i=0; i < this.slots.length; i++)
            this.slots[i] = new Slot_4652(this, data.slots[i]);
        this.setup_config_page();
    };
    slots_elements() {
        var el = document.createElement('div');
        for(var i=0; i<this.slots.length;i++) {
            var slot_el = this.slots[i].slot_elements();
            if ((slot_el !== undefined) && (slot_el !== null))
                el.appendChild(slot_el);
        }
        return el;
    };
}