import * as ajax from './ajax.js';
import * as tree from './tree_control.js';

class Gateway {
    constructor(gateway) {
        this.tree_item = null;
        this.display_name = gateway.display_name;
        this.model = gateway.model;
    };
    get_tree_item() {
        if (this.tree_item === null) {
            var item = new tree.TreeItem(this.display_name, this.model);
            this.tree_item = item;
        }
        return this.tree_item;
    }
}

class Device {
    constructor(devices, data) {
        this.tree_item = null;
        this.devices = devices;
        this.label = data.id;
        this.icon = data.icon;
    };
    get_tree_item() {
        if (this.tree_item === null) {
            var item = new tree.TreeItem(this.label, this.icon);
            var device = this;
            var click_func = function() {
                device.click();
            }
            item.on_click(click_func);
            this.tree_item = item;
        }
        return this.tree_item;
    };
    click() {
        console.log(this.label, 'clicked')
    }
}

class Devices {
    constructor(system) {
        this.tree_item = null;
        this.system = system;
        this.devices = []
    }
    get_tree_item() {
        if (this.tree_item === null) {
            var devices = this
            var item = new tree.TreeItem('Devices');
            this.tree_item = item;
            ajax.get_json('/api/get-system-devices?system_id='+this.system.system_id,
                function(data) {
                    if (data.ok !== undefined && data.ok === true) {
                        devices.update_device_list(data);
                    }
                });
        }
        return this.tree_item;
    }
    update_device_list(devices){
        if ((devices.ok !== undefined) && (devices.ok)){
            devices = devices.devices;
            this.devices = [];
            this.tree_item.empty()
            devices.forEach(data => {
                var device = new Device(this, data);
                this.devices.push(device);
                var elem = device.get_tree_item();
                this.tree_item.append_item(elem);
            });
        }

    }
}

class System {
    constructor(system) {
        this.tree_item = null;
        this.system_id = system.id;
        this.display_name = system.display_name;
        this.gateway = new Gateway(system.gateway)
        this.devices = new Devices(this);
    }
    get_tree_item() {
        if (this.tree_item === null) {
            var item = new tree.TreeItem(this.display_name, 'house');
            item.append_item(this.gateway.get_tree_item());
            item.append_item(this.devices.get_tree_item());
            this.tree_item = item;
        }
        return this.tree_item;
    }
    update_devices() {

    }
}

class App {
    constructor () {
        this.main_tree = new tree.TreeControl("object-tree");
        this.content_pane = "main-content";
        this.systems = new Array();
    }; 
    start(){
        let app = this;
        let systems = this.systems;
        ajax.get_json('/api/get-systems-list', function (data) {
            data.forEach(sys_data => {
                var system = new System(sys_data);
                app.add_system(system);
            });
        });
    };
    add_system(system) {
        if (system !== null) {
            this.systems.push(system);
            var item = system.get_tree_item();
            this.main_tree.add_item(item);
        }
    };
}

let Application = new App();

function load_app() {
    Application.start();
}


function ready(fn) {
    if (document.readyState === "complete") {
        fn();
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
}

ready(load_app);

