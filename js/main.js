'use strict'

$(document).ready(function() {
    var global = {};

    var trunk = {};
    trunk.width = 340;
    trunk.height = 200;
    trunk.left = 35;
    trunk.right = 10;
    trunk.xax_count = 5;

    var days_shown = 126; // 3 release cycles
    var split_by_data;

    assignEventListeners();

    //set markers
    var markers = [{
        'date': new Date('2014-03-18'),
        'label': '29 beta'
    }, {
        'date': new Date('2014-04-29'),
        'label': '29'
    }, {
        'date': new Date('2014-05-09'),
        'label': '29 ga'
    }, {
        'date': new Date('2014-06-10'),
        'label': '30'
    }, {
        'date': new Date('2014-06-17'),
        'label': '30 ga'
    }, {
        'date': new Date('2014-07-22'),
        'label': '31'
    }, {
        'date': new Date('2014-07-29'),
        'label': '31 ga'
    }, {
        'date': new Date('2014-09-02'),
        'label': '32'
    }, {
        'date': new Date('2014-09-12'),
        'label': '32 ga'
    }, {
        'date': new Date('2014-10-14'),
        'label': '33'
      }, {
        'date': new Date('2014-11-10'),
        'label': '33.1'
    }, {
        'date': new Date('2014-12-01'),
        'label': '34'
    }];


    d3.json('data/output.json', function(data) {
        for(var i = 0; i < data.length; i++) {
            data[i] = MG.convert.date(data[i], 'date');
        }

        MG.data_graphic({
            title:"Market Share by Web Traffic",
            // description: "Try resizing your window.",
            data: data,
            chart_type:'missing-data',
            legend: ['Chrome','IE','Safari','Firefox'],
            legend_target: '.legend1',
            full_width: true,
            height: trunk.height * 6 / 4,
            right: trunk.right,
            x_extended_ticks: true,
            target: '#webtraffic',
            linked: true,
            x_accessor: 'date',
            y_accessor: 'value'
        });

        MG.data_graphic({
            title:"Market Share by Pageviews",
            // description: "Try resizing your window.",
            data: data,
            full_width: true,
            format: 'percentage',
            chart_type:'line',
            legend: ['Chrome','IE','Safari','Firefox'],
            legend_target: '.legend2',
            height: trunk.height * 6 / 4,
            right: trunk.right,
            x_extended_ticks: true,
            target: '#pageviews',
            linked: true,
            x_accessor: 'date',
            y_accessor: 'sc_value'
        });

        MG.data_graphic({
            title:"Market Share by Users",
            // description: "Try resizing your window.",
            data: data,
            full_width: true,
            interpolate: 'basic',
            format: 'percentage',
            legend: ['Chrome','IE','Safari','Firefox'],
            legend_target: '.legend3',
            height: trunk.height * 6 / 4,
            right: trunk.right,
            x_extended_ticks: true,
            target: '#users',
            linked: true,
            x_accessor: 'date',
            y_accessor: 'nms_value'
        });
    });


    function assignEventListeners() {
        $('#dark-css').click(function () {
            $('.missing')
                .css('background-image', 'url(images/missing-data-dark.png)');

            $('.transparent-rollover-rect')
                .attr('fill', 'white');

            $('.trunk-section')
                .css('border-top-color', '#5e5e5e');

            $('.pill').removeClass('active');

            $(this).toggleClass('active');

            $('#dark')
                .attr({href : 'css/metricsgraphics-dark.css'});

            return false;
        });

        $('#light-css').click(function () {
            $('.missing')
                .css('background-image', 'url(images/missing-data.png)');

            $('.transparent-rollover-rect')
                .attr('fill', 'black');

            $('.trunk-section')
                .css('border-top-color', '#ccc');

            $('.pill').removeClass('active');
            $(this).toggleClass('active');

            $('#dark').attr({href : ''});
            return false;
        });


    }

    function modify_time_period(data, past_n_days) {
        // splice time period
        var data_spliced = MG.clone(data);
        if (past_n_days !== '') {
            for (var i = 0; i < data_spliced.length; i++) {
                var from = data_spliced[i].length - past_n_days;
                data_spliced[i].splice(0,from);
            }
        }

        return data_spliced;
    }

    function addCommas(nStr) {
        nStr += '';
        var x = nStr.split('.');
        var x1 = x[0];
        var x2 = x.length > 1 ? '.' + x[1] : '';
        var rgx = /(\d+)(\d{3})/;
        while (rgx.test(x1)) {
            x1 = x1.replace(rgx, '$1' + ',' + '$2');
        }
        return x1 + x2;
    }

    var bdata = [
        {platform: 'mobile'},
        {platform: 'desktop'},
        {os: 'Windows'},
        {os: 'OS X'},
        {os: 'Linux'}
    ];

    var resolution_features = ['weekly', 'monthly', 'last 3 months'];

    var buttons = MG.button_layout('div#buttons')
        .data(bdata)
        .manual_button('Time Scale', resolution_features, function(){ console.log('switched time scales'); })
        .button('platform', 'Platform', function(){console.log('switched platform')})
        .button('os', 'OS', function(){console.log('switched os')})
        .button('country', 'Country')
        .callback(function(){console.log('replot')})
        .display();

        $('div.country-btns button').prop('disabled', true);
})
