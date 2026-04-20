from fasthtml.common import *
import matplotlib.pyplot as plt

# Import QueryBase, Employee, Team from employee_events
from employee_events.query_base import QueryBase
from employee_events.employee import Employee
from employee_events.team import Team

# import the load_model function from the utils.py file
from utils import load_model

"""
Below, we import the parent classes
you will use for subclassing
"""
from base_components import (
    Dropdown,
    BaseComponent,
    Radio,
    MatplotlibViz,
    DataTable
)

from combined_components import FormGroup, CombinedComponent


# Create a subclass of base_components/dropdown
# called `ReportDropdown`
class ReportDropdown(Dropdown):

    # Overwrite the build_component method
    # ensuring it has the same parameters
    # as the Report parent class's method
    def build_component(self, asset_id, model):
        #  Set the `label` attribute so it is set
        #  to the `name` attribute for the model
        self.label = model.name
        return super().build_component(asset_id, model)

    # Overwrite the `component_data` method
    # Ensure the method uses the same parameters
    # as the parent class method
    def component_data(self, asset_id, model):
        # Using the model argument
        # call the employee_events method
        # that returns the user-type's
        # names and ids
        return model.names()


# Create a subclass of base_components/BaseComponent
# called `Header`
class Header(BaseComponent):
    # Overwrite the `build_component` method
    # Ensure the method has the same parameters
    # as the parent class
    def build_component(self, asset_id, model):

        # Using the model argument for this method
        # return a fasthtml H1 objects
        # containing the model's name attribute

        # I resolve the display name from the model
        name_map = {v: k for k, v in model.names()}
        display_name = name_map.get(asset_id, "")

        # Then Build a clear title (with specific name of employee or team)
        if display_name:
            title = f"{model.name.capitalize()}: {display_name}"
        else:
            title = f"{model.name.capitalize()} dashboard"

        return H1(title)


# Create a subclass of base_components/MatplotlibViz
# called `LineChart`
class LineChart(MatplotlibViz):

    # Overwrite the parent class's `visualization`
    # method. Use the same parameters as the parent
    def visualization(self, asset_id, model):

        # Pass the `asset_id` argument to
        # the model's `event_counts` method to
        # receive the x (Day) and y (event count)
        df = model.event_counts(asset_id)

        # Use the pandas .fillna method to fill nulls with 0
        df = df.fillna(0)

        # User the pandas .set_index method to set
        # the date column as the index
        df = df.set_index("event_date")

        # Sort the index
        df = df.sort_index()

        # Use the .cumsum method to change the data
        # in the dataframe to cumulative counts
        df = df.cumsum()

        # Set the dataframe columns to the list
        # ['Positive', 'Negative']
        df.columns = ["Positive", "Negative"]

        # Initialize a pandas subplot
        # and assign the figure and axis
        # to variables
        fig, ax = plt.subplots()

        # call the .plot method for the
        # cumulative counts dataframe
        df.plot(ax=ax)

        # pass the axis variable
        # to the `.set_axis_styling`
        # method
        # Use keyword arguments to set
        # the border color and font color to black.
        # Reference the base_components/matplotlib_viz file
        # to inspect the supported keyword arguments
        self.set_axis_styling(ax, bordercolor="black", fontcolor="black")

        # Set title and labels for x and y axis
        ax.set_title("Cumulative Events")
        ax.set_xlabel("Date")
        ax.set_ylabel("Event Count")
        return fig


# Create a subclass of base_components/MatplotlibViz
# called `BarChart`
class BarChart(MatplotlibViz):

    # Create a `predictor` class attribute
    # assign the attribute to the output
    # of the `load_model` utils function
    predictor = load_model()

    # Overwrite the parent class `visualization` method
    # Use the same parameters as the parent
    def visualization(self, asset_id, model):

        # Using the model and asset_id arguments
        # pass the `asset_id` to the `.model_data` method
        # to receive the data that can be passed to the machine
        # learning model
        data = model.model_data(asset_id)

        # Using the predictor class attribute
        # pass the data to the `predict_proba` method
        proba = self.predictor.predict_proba(data)

        # Index the second column of predict_proba output
        # The shape should be (<number of records>, 1)
        proba = proba[:, 1]

        # Below, create a `pred` variable set to
        # the number we want to visualize
        #
        # If the model's name attribute is "team"
        # We want to visualize the mean of the predict_proba output
        if model.name == "team":
            pred = proba.mean()

        # Otherwise set `pred` to the first value
        # of the predict_proba output
        else:
            pred = proba[0]

        # Initialize a matplotlib subplot
        fig, ax = plt.subplots()

        # Run the following code unchanged
        ax.barh([''], [pred])
        ax.set_xlim(0, 1)
        ax.set_title('Predicted Recruitment Risk', fontsize=20)

        # pass the axis variable
        # to the `.set_axis_styling`
        # method
        self.set_axis_styling(ax, bordercolor="black", fontcolor="black")
        return fig


# Create a subclass of combined_components/CombinedComponent
# called Visualizations
class Visualizations(CombinedComponent):

    # Set the `children`
    # class attribute to a list
    # containing an initialized
    # instance of `LineChart` and `BarChart`
    children = [LineChart(), BarChart()]

    # Leave this line unchanged
    outer_div_type = Div(cls='grid')


# Create a subclass of base_components/DataTable
# called `NotesTable`
class NotesTable(DataTable):

    # Overwrite the `component_data` method
    # using the same parameters as the parent class
    def component_data(self, entity_id, model):

        # Using the model and entity_id arguments
        # pass the entity_id to the model's .notes
        # method. Return the output
        return model.notes(entity_id)


class DashboardFilters(FormGroup):

    id = "top-filters"
    action = "/update_data"
    method = "POST"

    children = [
        Radio(
            values=["Team", "Employee"],
            name="profile_type",
            hx_get="/update_dropdown",
            hx_target="#selector"
        ),
        ReportDropdown(
            id="selector",
            name="user-selection"
        ),

        # Added this script to fully realign client-side state after every full page load
        # and to make the app work correctly both at "/" and under "/proxy/<port>/".
        #
        # Background problem:
        # - The form submits with POST /update_data and the backend responds with a 303 redirect
        #   to /employee/{id} or /team/{id}.
        # - After a 303, the browser performs a fresh GET and the client state is reset:
        #     * the Radio component resets to its default (Employee),
        #     * but the Dropdown may keep the previous state (Team / Employee).
        # - HTMX may then re-trigger /update_dropdown using that stale client state,
        #   producing inconsistent UI state and potential crashes.
        #
        # I couldn't solve it server-side:
        # - After a redirect, the browser is authoritative over component state.
        # - Rebuilding components or forcing values on the server cannot override
        #   what the client restores after a full navigation.
        #
        # So, what this script does:
        # 1) Detects whether the app is running at "/" or under "/proxy/<port>/" by inspecting
        #    window.location.pathname and computes the correct app root.
        # 2) Patches client-side absolute URLs so they work under a proxy:
        #    - Rewrites hx-get="/update_dropdown" to include the app root.
        #    - Rewrites form action="/update_data" to include the app root.
        # 3) Intercepts the form submit to avoid relying on server-side 303 redirects
        #    that point to absolute paths ("/employee/{id}", "/team/{id}") which would
        #    escape the proxy.
        #    Instead, it:
        #      - POSTs the form data,
        #      - then navigates explicitly to the correct target URL under the same app root.
        # 4) On every full page load (DOMContentLoaded), explicitly fetches
        #    /update_dropdown?profile_type=Employee (with the correct prefix) and replaces
        #    the dropdown HTML, ensuring that:
        #      - the radio defaults to Employee,
        #      - the dropdown is also reset to Employee,
        #      - both components are always in sync after reloads and redirects.
        #
        # Result:
        # - Radio and dropdown are always aligned.
        # - No stale HTMX calls after redirects.
        # - Works identically at "/" and "/proxy/<port>/".
        # - No dependency on hidden build_component behavior.
        #
        Script(r"""
document.addEventListener('DOMContentLoaded', function () {
    // --- 1) Detect app root: "" or "/proxy/<port>" ---
    const path = window.location.pathname;
    const match = path.match(/^\/(proxy\/\d+)(\/|$)/);
    const appRoot = match ? '/' + match[1] : '';

    // Prefix helper (expects a leading "/")
    const pref = (p) => appRoot + p;

    // --- 2) Fix HTMX endpoint on radio change (hx-get) ---
    // Your Radio was created with hx_get="/update_dropdown"
    document.querySelectorAll('[hx-get="/update_dropdown"]').forEach(el => {
        el.setAttribute('hx-get', pref('/update_dropdown'));
    });

    // Re-process DOM for htmx after patching attributes (if htmx exists)
    if (window.htmx) window.htmx.process(document.body);

    // --- 3) Fix form action so POST goes to the right place under proxy ---
    // Your FormGroup id is "top-filters" and action="/update_data"
    const form = document.getElementById('top-filters');
    if (form) {
        form.setAttribute('action', pref('/update_data'));

        // --- 4) Intercept submit to avoid proxy-breaking 303 redirect ---
        // Backend redirects to "/employee/{id}" or "/team/{id}" (absolute),
        // so under proxy we'd escape. We'll navigate ourselves with appRoot.
        form.addEventListener('submit', async function (e) {
            e.preventDefault();

            const fd = new FormData(form);
            const profileType = fd.get('profile_type');
            const id = fd.get('user-selection');

            // POST to correct endpoint (under proxy if needed)
            await fetch(pref('/update_data'), {
                method: 'POST',
                body: fd,
                credentials: 'same-origin'
            });

            // Navigate explicitly under the same appRoot
            const target = (profileType === 'Team')
                ? pref('/team/' + id)
                : pref('/employee/' + id);

            window.location.assign(target);
        }, { once: true });
    }

    // --- 5) Keep your original reset dropdown after full page load (prefixed) ---
    fetch(pref('/update_dropdown') + '?profile_type=Employee')
        .then(r => r.text())
        .then(html => {
            const el = document.getElementById('selector');
            if (el) el.outerHTML = html;
        });
});
""")
    ]

    # This I need it so dropdown loads alright in the first load of browser
    def build_component(self, asset_id, model):
        emp = Employee()
        first_emp_id = emp.names()[0][1]  # (full_name, employee_id)

        return super().build_component(first_emp_id, emp)


# Create a subclass of CombinedComponents
# called `Report`
class Report(CombinedComponent):

    # Set the `children`
    # class attribute to a list
    # containing initialized instances
    # of the header, dashboard filters,
    # data visualizations, and notes table
    children = [Header(), DashboardFilters(), Visualizations(), NotesTable()]


# Initialize a fasthtml app
app = FastHTML()

# Initialize the `Report` class
report = Report()


# Create a route for a get request
# Set the route's path to the root
@app.get("/")

    # Call the initialized report
    # pass the integer 1 and an instance
    # of the Employee class as arguments
    # Return the result
def get():
    return report(1, Employee())


# Create a route for a get request
# Set the route's path to receive a request
# for an employee ID so `/employee/2`
# will return the page for the employee with
# an ID of `2`.
# parameterize the employee ID
# to a string datatype
@app.get("/employee/{id}")

    # Call the initialized report
    # pass the ID and an instance
    # of the Employee SQL class as arguments
    # Return the result
def get(id: str):
    return report(int(id), Employee())


# Create a route for a get request
# Set the route's path to receive a request
# for a team ID so `/team/2`
# will return the page for the team with
# an ID of `2`.
# parameterize the team ID
# to a string datatype
@app.get("/team/{id}")

    # Call the initialized report
    # pass the id and an instance
    # of the Team SQL class as arguments
    # Return the result
def get(id: str):
    return report(int(id), Team())


# Keep the below code unchanged!
@app.get('/update_dropdown{r}')
def update_dropdown(r):
    dropdown = DashboardFilters.children[1]
    print('PARAM', r.query_params['profile_type'])
    if r.query_params['profile_type'] == 'Team':
        return dropdown(None, Team())
    elif r.query_params['profile_type'] == 'Employee':
        return dropdown(None, Employee())


@app.post('/update_data')
async def update_data(r):
    from fasthtml.common import RedirectResponse
    data = await r.form()
    profile_type = data._dict['profile_type']
    id = data._dict['user-selection']
    if profile_type == 'Employee':
        return RedirectResponse(f"/employee/{id}", status_code=303)
    elif profile_type == 'Team':
        return RedirectResponse(f"/team/{id}", status_code=303)


serve()
