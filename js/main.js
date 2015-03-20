// 'use strict'

$(document).ready(function() {
    var global = {};
    global.loaded = false;
    global.os = 'all';
    global.geo = 'all';
    global.platform = 'desktop';
    global.timescale = 'weekly';

    trunk = {};
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

    var platformMap = {
      users: {
        'mobile+tablet': 'mobile_and_tablet',
        'desktop': 'desktop'
      },
      pageviews: {
        'mobile+tablet': 'mobile%2Btablet',
        'desktop': 'desktop'
      }
    }

    function custom_sort(a, b) {
        return new Date(a.date).getTime() - new Date(b.date).getTime();
    }

    function plot() {
      // d3.json('data/weekly_data.json', function(data) {
      d3.json('data/' + global.timescale + '_data.json', function(data) {

          var pageviews = crossfilter(data['pageviews']);
          var pageviewsByOS = pageviews.dimension(function(p) { return p.os } );
          var pageviewsByPlatform = pageviews.dimension(function(p) { return p.platform } );
          var users = crossfilter(data['users']);
          var usersByOS = users.dimension(function(p) { return p.os } );
          var usersByPlatform = users.dimension(function(p) { return p.platform } );

          pageviewsByOS.filterExact('all');
          pageviewsByPlatform.filterExact(platformMap['pageviews'][global.platform]);
          usersByOS.filterExact('all');
          usersByPlatform.filterExact(platformMap['users'][global.platform]);

          var pageview_data = pageviewsByPlatform.top(Infinity);
          var user_data = usersByPlatform.top(Infinity);
          pageview_data.sort(custom_sort);
          user_data.sort(custom_sort);
          pageview_data = modify_time_period([MG.convert.date(pageview_data, 'date')], 52);
          user_data = modify_time_period([MG.convert.date(user_data, 'date')], 52);


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
              data: pageview_data,
              full_width: true,
              format: 'percentage',
              chart_type:'line',
              legend: ['IE', 'Chrome', 'Opera', 'Firefox', 'Safari', 'Other'],
              legend_target: '.legend2',
              height: trunk.height * 6 / 4,
              right: trunk.right,
              x_extended_ticks: true,
              target: '#pageviews',
              linked: true,
              x_accessor: 'date',
              y_accessor: ['IE', 'Chrome', 'Opera', 'Firefox', 'Safari', 'Other']
          });

          MG.data_graphic({
              title:"Market Share by Pageviews",
              // description: "Try resizing your window.",
              data: pageview_data,
              full_width: true,
              format: 'percentage',
              chart_type:'line',
              legend: ['IE', 'Chrome', 'Opera', 'Firefox', 'Safari', 'Other'],
              legend_target: '.legend2',
              height: trunk.height * 6 / 4,
              right: trunk.right,
              x_extended_ticks: true,
              target: '#pageviews',
              linked: true,
              x_accessor: 'date',
              y_accessor: ['IE', 'Chrome', 'Opera', 'Firefox', 'Safari', 'Other']
          });

          MG.data_graphic({
              title:"Market Share by Users",
              // description: "Try resizing your window.",
              data: user_data,
              full_width: true,
              interpolate: 'basic',
              format: 'percentage',
              legend: ['IE','Chrome','Opera','Firefox', 'Safari', 'Other'],
              legend_target: '.legend3',
              height: trunk.height * 6 / 4,
              right: trunk.right,
              x_extended_ticks: true,
              target: '#users',
              linked: true,
              x_accessor: 'date',
              y_accessor: ['IE', 'Chrome', 'Opera', 'Firefox', 'Safari', 'Other']
          });

          global.loaded = true;
      });
    }

    plot("desktop");


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
        {platform: 'mobile+tablet'},
        {platform: 'desktop'},
        {os: 'Windows'},
        {os: 'OS X'},
        {os: 'Linux'}
    ];

    var resolution_features = ['weekly', 'monthly'];

    function update(dimension, platform) {
      // console.log("update", dimension, platform);
      global.platform = platform;
      plot();
    }

    function set_parameters(which) {
      if (!global.loaded) {
        return;
      }
      console.log('set parameters', which);
      global.timescale = which;
      plot();
    }

    var buttons = MG.button_layout('div#buttons')
        .data(bdata)
        .manual_button('Time Scale', resolution_features, set_parameters)
        .button('platform', 'Platform', set_parameters)
        .button('os', 'OS', set_parameters)
        .button('country', 'Country', set_parameters)
        .callback(update)
        .display();

        // $('div.platform-btns button').prop('disabled', true);
        $('div.os-btns button').prop('disabled', true);
        $('div.country-btns button').prop('disabled', true);
})
