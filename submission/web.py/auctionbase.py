#!/usr/bin/env python

import sys; sys.path.insert(0, 'lib') # this line is necessary for the rest
import os                             # of the imports to work!

import web
import sqlitedb
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

###########################################################################################
##########################DO NOT CHANGE ANYTHING ABOVE THIS LINE!##########################
###########################################################################################

######################BEGIN HELPER METHODS######################

# helper method to convert times from database (which will return a string)
# into datetime objects. This will allow you to compare times correctly (using
# ==, !=, <, >, etc.) instead of lexicographically as strings.

# Sample use:
# current_time = string_to_time(sqlitedb.getTime())

def string_to_time(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

# helper method to render a template in the templates/ directory
#
# `template_name': name of template file to render
#
# `**context': a dictionary of variable names mapped to values
# that is passed to Jinja2's templating engine
#
# See curr_time's `GET' method for sample usage
#
# WARNING: DO NOT CHANGE THIS METHOD
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(autoescape=True,
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)

    web.header('Content-Type','text/html; charset=utf-8', unique=True)

    return jinja_env.get_template(template_name).render(context)

#####################END HELPER METHODS#####################

urls = ('/currtime', 'curr_time',
        '/selecttime', 'select_time',
        '/search', 'search',
        '/add_bid', 'add_bid',
        '/', 'home',
        '/detail(.*)', 'detail'
        # TODO: add additional URLs here
        # first parameter => URL, second parameter => class name
        )

class curr_time:
    # A simple GET request, to '/currtime'
    #
    # Notice that we pass in `current_time' to our `render_template' call
    # in order to have its value displayed on the web page
    def GET(self):
        current_time = sqlitedb.getTime()
        return render_template('curr_time.html', time = current_time)

class home:
    def GET(self):
        return render_template('home.html')

class search:
    def GET(self):
        return render_template('search.html')

    def POST(self):
        try:
            search_params = web.input()
            item_id = search_params['itemID']
            user_id = search_params['userID']
            min_price = search_params['minPrice']
            max_price = search_params['maxPrice']
            status = search_params['status']
            desc = search_params['description']
            category = search_params['category']
            items = []

            items = sqlitedb.getItemsOnSearch(item_id, user_id, min_price, max_price, status, desc, category)
            message = 'Success ! Retreived ' + str(len(items)) + ' results.'

        except Exception as e:
            message = str(e)

        return render_template('search.html', search_result=items, message=message, search=search_params)

class detail:
    def GET(self, item):
        auction = web.input(item=None)
        detail = sqlitedb.getItemById(auction.item)
        categories = sqlitedb.getCategoriesByItemId(auction.item)
        status = sqlitedb.getStatusByItemId(auction.item)
        bids = sqlitedb.getBidsByItemId(auction.item)
        return render_template('detail.html', status=status, bids=bids, categories=categories, details=detail)

class select_time:
    # Another GET request, this time to the URL '/selecttime'
    def GET(self):
        return render_template('select_time.html')

    #
    # You can fetch the parameters passed to the URL
    # by calling `web.input()' for **both** POST requests
    # and GET requests
    def POST(self):
        post_params = web.input()
        MM = post_params['MM']
        dd = post_params['dd']
        yyyy = post_params['yyyy']
        HH = post_params['HH']
        mm = post_params['mm']
        ss = post_params['ss'];
        enter_name = post_params['entername']


        selected_time = '%s-%s-%s %s:%s:%s' % (yyyy, MM, dd, HH, mm, ss)
        update_message = '(Thank you for changing the time %s. The new time selected is: %s.)' % (enter_name, selected_time)

        t = sqlitedb.transaction()
        query_string = 'update CurrentTime set Time = $time'
        try:
            sqlitedb.db.query(query_string, {'time': selected_time})
        except Exception as e:
            t.rollback()
            update_message = str(e)
        else:
            t.commit()
        # Here, we assign `update_message' to `message', which means
        # we'll refer to it in our template as `message'
        return render_template('select_time.html', message = update_message)    

###########################################################################################
##########################DO NOT CHANGE ANYTHING BELOW THIS LINE!##########################
###########################################################################################

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
