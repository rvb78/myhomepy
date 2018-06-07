import * as base from './base_device_model.js';

export class Device_4693 extends base.Base_Device_Model {
    constructor(data) {
        super(data);
    };
}

Device_4693.prototype._device_types = {
    21 : {
        nb_slots : 1,
        references : {
            'BRAND_UNDEFINED' : {
                icon: 'unknown-1',
                0 : '<unknown>'
            },
            'BRAND_BTICINO' : {
                icon: 'BTicino',
                3 : 'Axolute H4693'
            },
            'BRAND_LEGRAND' : {
                icon: 'Legrand',
                4 : 'Céliane 067458'
            }
        }
    }
};