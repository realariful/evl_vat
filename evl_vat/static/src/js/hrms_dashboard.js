odoo.define('evl_vat.Dashboard', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var rpc = require('web.rpc');
var session = require('web.session');
var web_client = require('web.web_client');
var _t = core._t;
var QWeb = core.qweb;

var HrDashboard = AbstractAction.extend({
    template: 'VatDashboardMain',
    cssLibs: [
        '/evl_vat/static/src/css/lib/nv.d3.css'
    ],
    jsLibs: [
        '/evl_vat/static/src/js/lib/d3.min.js'
    ],
    events: {
        
        'click .vat_balance': 'vat_balance',
        'click .vds_balance': 'vds_balance',
        'click .sale_order':'sale_order',
        'click .purchase_order':'purchase_order',
        'click .pur_tot':'pur_tot',
        'click .sale_tot':'sale_tot',
    },

    init: function(parent, context) {
        this._super(parent, context);
        this.date_range = 'week';  // possible values : 'week', 'month', year'
        this.date_from = moment().subtract(1, 'week');
        this.date_to = moment();
        this.dashboards_templates = ['LoginEmployeeDetails', 'ManagerDashboard', 'EmployeeDashboard'];
        this.employee_birthday = [];
        this.upcoming_events = [];
        this.announcements = [];
    console.log("INIT FUNCTION 1")
    },

    willStart: function() {
        console.log("WILLSTART FUNCTION")
        var self = this;
//        return $.when(ajax.loadLibs(this), this._super()).then(function() {console.log("test")
            return self.fetch_data();
//        });
    },

    start: function() {
        console.log("START FUNCTION")
        var self = this;
        this.set("title", 'Dashboard');
        return this._super().then(function() {
            self.update_cp();
            self.render_dashboards();
            self.render_graphs();
            self.$el.parent().addClass('oe_background_grey');
        });
    },

    // fetch_data: function() {
    //     console.log("FETCH_DATE FUNCTION")
    //     var self = this;
    //     var def1 =  this._rpc({
    //             model: 'vat.dashboard',
    //             method: 'get_user_employee_details'
    //     }).then(function(result) {
    //         self.login_employee =  result[0];
    //     });
    //     var def2 = self._rpc({
    //         model: "vat.dashboard",
    //         method: "get_upcoming",
    //     })
    //     .then(function (res) {
    //         self.employee_birthday = res['birthday'];
    //         self.upcoming_events = res['event'];
    //         self.announcements = res['announcement'];
    //     });
    //     return $.when(def1, def2);
    // },


    // Modified by Real
    fetch_data: function() {
        var self = this;
        var def1 =  this._rpc({
            model: 'vat.dashboard',
            method: 'get_user_employee_details'
        }).then(function(result) {
            self.login_employee =  result[0];
        });
        var def2 = self._rpc({
            model: "purchase.order",
            method: "get_purchase_details",
        })
        .then(function (res) {
            self.name = res['pur_name'];
            self.date_order = res['date_order'];
        });
        return $.when(def1, def2);
    },

    
    render_dashboards: function() {console.log("RENDER_DASHBOARD")
        var self = this;
        if (this.login_employee){
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}));
            });
            }
        else{
            self.$('.o_hr_dashboard').append(QWeb.render('EmployeeWarning', {widget: self}));
            }
    },

    render_graphs: function(){console.log("RENDER_GRAPHS")
        var self = this;
        if (this.login_employee){
            // self.render_department_employee();
            self.update_vat_balance();
            self.vat_vs_vds();
            // self.render_leave_graph();            
            // self.update_monthly_attrition();
            // self.update_leave_trend();
            

            
        }
    },

    on_reverse_breadcrumb: function() {console.log("ON_REVERSE_BREADCRUMB")
        var self = this;
        web_client.do_push_state({});
        this.update_cp();
        this.fetch_data().then(function() {
            self.$('.o_hr_dashboard').empty();
            self.render_dashboards();
            self.render_graphs();
        });
    },

    update_cp: function() {
        var self = this;
        console.log("UPDATE_CP")
//        this.update_control_panel(
//            {breadcrumbs: self.breadcrumbs}, {clear: true}
//        );
    },

    get_emp_image_url: function(employee){
        return window.location.origin + '/web/image?model=vat.dashboard&field=image&id='+employee;
    },

    update_attendance: function () {
        var self = this;
        this._rpc({
            model: 'vat.dashboard',
            method: 'attendance_manual',
            args: [[self.login_employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
        })
        .then(function(result) {
            var attendance_state =self.login_employee.attendance_state;
            var message = ''
            var action_client = {
                type: "ir.actions.client",
                name: _t('Dashboard '),
                tag: 'hr_dashboard',
            };
            self.do_action(action_client, {clear_breadcrumbs: true});
            if (attendance_state == 'checked_in'){
                message = 'Checked Out'
            }
            else if (attendance_state == 'checked_out'){
                message = 'Checked In'
            }
            self.trigger_up('show_effect', {
                message: _t("Successfully " + message),
                type: 'rainbow_man'
            });
        });

    },

    hr_payslip: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Employee Payslips"),
            type: 'ir.actions.act_window',
            res_model: 'sale.order',
            view_mode: 'tree,form,calendar',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id','=', this.login_employee.id]],
            target: 'current'
        }, options)
    },




    // Modified
    //--------------------------
    sale_order: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Sale Order"),
            type: 'ir.actions.act_window',
            res_model: 'sale.order',
            view_mode: 'tree,form,calendar',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id','=', this.login_employee.sale_id]],
            target: 'current'
        }, options)

    },
    sale_tot: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Sale Order"),
            type: 'ir.actions.act_window',
            res_model: 'sale.order',
            view_mode: 'tree,form,calendar',
            views: [[false, 'list'],[false, 'form']],
            domain: [],
            target: 'current'
        }, options)

    },
    purchase_order: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Purchase Order"),
            type: 'ir.actions.act_window',
            res_model: 'purchase.order',
            view_mode: 'tree,form,calendar',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id','=',this.login_employee.pur_id]],
            target: 'current'
        }, options)

    },
    pur_tot: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Purchase Order"),
            type: 'ir.actions.act_window',
            res_model: 'purchase.order',
            view_mode: 'tree,form,calendar',
            views: [[false, 'list'],[false, 'form']],
            domain: [],
            target: 'current'
        }, options)

    },   
    vat_balance: function(e) {
        var self = this;
       e.stopPropagation();
       e.preventDefault();
       var options = {
           on_reverse_breadcrumb: this.on_reverse_breadcrumb,
       };
       this.do_action({
           name: _t("VAT Payments"),
           type: 'ir.actions.act_window',
           res_model: 'evl.payments',
           view_mode: 'tree,form',
           views: [[false, 'list'], [false, 'form']],
           context: {
               'search_default_month': true,
           },
           domain: [],
           target: 'current'
       }, options)
   }, 
   

   vds_balance: function(e) {
    var self = this;
   e.stopPropagation();
   e.preventDefault();
   var options = {
       on_reverse_breadcrumb: this.on_reverse_breadcrumb,
   };
   this.do_action({
       name: _t("VDS Payments"),
       type: 'ir.actions.act_window',
       res_model: 'evl.vdspayments',
       view_mode: 'tree,form',
       views: [[false, 'list'], [false, 'form']],
       context: {
           'search_default_month': true,
       },
       domain: [],
       target: 'current'
   }, options)
}, 
 



    vat_vs_vds: function(){
    var elem = this.$('.join_resign_trend');
    var colors = ['#70cac1', '#659d4e', '#208cc2', '#4d6cb1', '#584999', '#8e559e' ];
    // '#cf3650', '#f65337', '#fe7139',
    // '#ffa433', '#ffc25b', '#f8e54b'];
    var color = d3.scale.ordinal().range(colors);
    rpc.query({
        model: "vat.dashboard",
        method: "vat_vs_vds",
    }).then(function (data) {
        data.forEach(function(d) {
          d.values.forEach(function(d) {
            d.l_month = d.l_month;
            d.count = +d.count;
          });
        });
        var margin = {top: 30, right: 10, bottom: 30, left: 30},
            width = 400 - margin.left - margin.right,
            height = 250 - margin.top - margin.bottom;

            // if (width > 300) {
            //     width = 300;
            //   } else {
            //   }
                          console.log("DATAS");
            console.log(width);console.log(height);
            // maxWidth: 400;
        // Set the ranges
        var x = d3.scale.ordinal()
            .rangeRoundBands([0, width], 1);

        var y = d3.scale.linear()
            .range([height, 0]);

        // Define the axes
        var xAxis = d3.svg.axis().scale(x)
            .orient("bottom");

        var yAxis = d3.svg.axis().scale(y)
            .orient("left").ticks(5);

        x.domain(data[0].values.map(function(d) { return d.l_month; }));
        y.domain([0, d3.max(data[0].values, d => d.count)])

        var svg = d3.select(elem[0]).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // Add the X Axis
        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);

        // Add the Y Axis
        svg.append("g")
            .attr("class", "y axis")
            .call(yAxis);


        var line = d3.svg.line()
            .x(function(d) {return x(d.l_month); })
            .y(function(d) {return y(d.count); });

        let lines = svg.append('g')
          .attr('class', 'lines');

        lines.selectAll('.line-group')
            .data(data).enter()
            .append('g')
            .attr('class', 'line-group')
            .append('path')
            .attr('class', 'line')
            .attr('d', function(d) { return line(d.values); })
            .style('stroke', (d, i) => color(i));

        lines.selectAll("circle-group")
            .data(data).enter()
            .append("g")
            .selectAll("circle")
            .data(function(d) { return d.values;}).enter()
            .append("g")
            .attr("class", "circle")
            .append("circle")
            .attr("cx", function(d) { return x(d.l_month)})
            .attr("cy", function(d) { return y(d.count)})
            .attr("r", 3);

        var legend = d3.select(elem[0]).append("div").attr('class','legend');

        var tr = legend.selectAll("div").data(data).enter().append("div");

        tr.append("span").attr('class','legend_col').append("svg").attr("width", '16').attr("height", '16').append("rect")
            .attr("width", '16').attr("height", '16')
            .attr("fill",function(d, i){ return color(i) });

        tr.append("span").attr('class','legend_col').text(function(d){ return d.name;});
    });
},



    // update_monthly_attrition: function(){
    //     var elem = this.$('.attrition_rate');
    //     var colors = ['#70cac1', '#659d4e', '#208cc2', '#4d6cb1', '#584999', '#8e559e', '#cf3650', '#f65337', '#fe7139',
    //     '#ffa433', '#ffc25b', '#f8e54b'];
    //     var color = d3.scale.ordinal().range(colors);
    //     rpc.query({
    //         model: "vat.dashboard",
    //         method: "get_attrition_rate",
    //     }).then(function (data) {
    //         var margin = {top: 30, right: 20, bottom: 30, left: 80},
    //             width = 500 - margin.left - margin.right,
    //             height = 250 - margin.top - margin.bottom;

    //         // Set the ranges
    //         var x = d3.scale.ordinal()
    //             .rangeRoundBands([0, width], 1);

    //         var y = d3.scale.linear()
    //             .range([height, 0]);

    //         // Define the axes
    //         var xAxis = d3.svg.axis().scale(x)
    //             .orient("bottom");

    //         var yAxis = d3.svg.axis().scale(y)
    //             .orient("left").ticks(5);

    //         var valueline = d3.svg.line()
    //             .x(function(d) { return x(d.month); })
    //             .y(function(d) { return y(d.attrition_rate); });


    //         var svg = d3.select(elem[0]).append("svg")
    //             .attr("width", width + margin.left + margin.right)
    //             .attr("height", height + margin.top + margin.bottom)
    //             .append("g")
    //             .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    //         x.domain(data.map(function(d) { return d.month; }));
    //         y.domain([0, d3.max(data, function(d) { return d.attrition_rate; })]);

    //         // Add the X Axis
    //         svg.append("g")
    //             .attr("class", "x axis")
    //             .attr("transform", "translate(0," + height + ")")
    //             .call(xAxis);

    //         // Add the Y Axis
    //         svg.append("g")
    //             .attr("class", "y axis")
    //             .call(yAxis);

    //         svg.append("path")
    //             .attr("class", "line")
    //             .attr("d", valueline(data));

    //         // Add the scatterplot
    //         svg.selectAll("dot")
    //             .data(data)
    //             .enter().append("circle")
    //             .attr("r", 3)
    //             .attr("cx", function(d) { return x(d.month); })
    //             .attr("cy", function(d) { return y(d.attrition_rate); })
    //             .on("mouseover", function() { tooltip.style("display", null);
    //                 d3.select(this).transition().duration(500).ease("elastic").attr('r', 3 * 2)
    //              })
    //             .on("mouseout", function() { tooltip.style("display", "none");
    //                 d3.select(this).transition().duration(500).ease("in-out").attr('r', 3)
    //             })
    //             .on("mousemove", function(d) {
    //                 var xPosition = d3.mouse(this)[0] - 15;
    //                 var yPosition = d3.mouse(this)[1] - 25;
    //                 tooltip.attr("transform", "translate(" + xPosition + "," + yPosition + ")");
    //                 tooltip.select("text").text(d.attrition_rate);
    //             });

    //         var tooltip = svg.append("g")
    //               .attr("class", "tooltip")
    //               .style("display", "none");

    //             tooltip.append("rect")
    //               .attr("width", 30)
    //               .attr("height", 20)
    //               .attr("fill", "black")
    //               .style("opacity", 0.5);

    //             tooltip.append("text")
    //               .attr("x", 15)
    //               .attr("dy", "1.2em")
    //               .style("text-anchor", "middle")
    //               .attr("font-size", "12px")
    //               .attr("font-weight", "bold");

    //     });
    // },


    // 
    update_vat_balance: function(){
        var elem = this.$('.update_vat');
        var colors = ['#70cac1', '#659d4e', '#208cc2', '#4d6cb1', '#584999', '#8e559e'];
        //  '#cf3650', '#f65337', '#fe7139',
        // '#ffa433', '#ffc25b', '#f8e54b'];
        var color = d3.scale.ordinal().range(colors);
        rpc.query({
            model: "vat.dashboard",
            method: "get_vat_balance",
        }).then(function (data) {
            var margin = {top: 30, right: 20, bottom: 30, left: 80},
                width = 500 - margin.left - margin.right,
                height = 250 - margin.top - margin.bottom;

            // Set the ranges
            var x = d3.scale.ordinal()
                .rangeRoundBands([0, width], 1);

            var y = d3.scale.linear()
                .range([height, 0]);

            // Define the axes
            var xAxis = d3.svg.axis().scale(x)
                .orient("bottom");

            var yAxis = d3.svg.axis().scale(y)
                .orient("left").ticks(5);

            var valueline = d3.svg.line()
                .x(function(d) { return x(d.l_month); })
                .y(function(d) { return y(d.vat); });


            var svg = d3.select(elem[0]).append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            x.domain(data.map(function(d) { return d.l_month; }));
            y.domain([0, d3.max(data, function(d) { return d.vat; })]);

            // Add the X Axis
            svg.append("g")
                .attr("class", "x axis")
                .attr("transform", "translate(0," + height + ")")
                .call(xAxis);

            // Add the Y Axis
            svg.append("g")
                .attr("class", "y axis")
                .call(yAxis);

            svg.append("path")
                .attr("class", "line")
                .attr("d", valueline(data));

            // Add the scatterplot
            svg.selectAll("dot")
                .data(data)
                .enter().append("circle")
                .attr("r", 3)
                .attr("cx", function(d) { return x(d.l_month); })
                .attr("cy", function(d) { return y(d.vat); })
                .on("mouseover", function() { tooltip.style("display", null);
                    d3.select(this).transition().duration(500).ease("elastic").attr('r', 3 * 2)
                 })
                .on("mouseout", function() { tooltip.style("display", "none");
                    d3.select(this).transition().duration(500).ease("in-out").attr('r', 3)
                })
                .on("mousemove", function(d) {
                    var xPosition = d3.mouse(this)[0] - 15;
                    var yPosition = d3.mouse(this)[1] - 25;
                    tooltip.attr("transform", "translate(" + xPosition + "," + yPosition + ")");
                    tooltip.select("text").text(d.vat);
                });

            var tooltip = svg.append("g")
                  .attr("class", "tooltip")
                  .style("display", "none");

                tooltip.append("rect")
                  .attr("width", 30)
                  .attr("height", 20)
                  .attr("fill", "black")
                  .style("opacity", 0.5);

                tooltip.append("text")
                  .attr("x", 15)
                  .attr("dy", "1.2em")
                  .style("text-anchor", "middle")
                  .attr("font-size", "12px")
                  .attr("font-weight", "bold");

        });
    },
 
});


core.action_registry.add('hr_dashboard', HrDashboard);

return HrDashboard;

});
