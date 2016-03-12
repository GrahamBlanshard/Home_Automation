package prograham.homecontrol;

import android.app.Activity;
import android.app.Fragment;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.speech.RecognizerIntent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.StringRequest;
import com.android.volley.toolbox.Volley;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.List;

public class GarageFragment extends Fragment {
    private MainActivity _parent;
    private Context _context;
    private SharedPreferences _sharedPrefs;
    private RequestQueue _requests;
    private boolean isOpen = false;
    private final int SPEECH_REQUEST_CODE = 4027;

    public GarageFragment() {
        // Required empty public constructor
    }

    public static GarageFragment newInstance(String param1, String param2) {
        GarageFragment fragment = new GarageFragment();
        Bundle args = new Bundle();
        fragment.setArguments(args);
        return fragment;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        _parent = (MainActivity)getActivity();
        _context = _parent.getBaseContext();
        _requests = Volley.newRequestQueue(_context);
        _sharedPrefs = PreferenceManager.getDefaultSharedPreferences(_context);
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        return inflater.inflate(R.layout.fragment_garage, container, false);
    }

    @Override
    public void onResume() {
        super.onResume();

        Button garageButton = (Button)_parent.findViewById(R.id.garage_move);
        Button voiceButton = (Button) _parent.findViewById(R.id.voice_button);

        garageButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                sendGarageCommand((isOpen ? "close" : "open"), true);
            }
        });

        voiceButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                        RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);

                startActivityForResult(intent, SPEECH_REQUEST_CODE);
            }
        });

        if (_requests == null) _requests = Volley.newRequestQueue(_context);
        refresh();
    }

    @Override
    public void onAttach(Context context) {
        super.onAttach(context);
    }

    @Override
    public void onDetach() {
        super.onDetach();
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
    }

    public void refresh() {
        sendGarageCommand("status", false);
    }

    private boolean sendGarageCommand(final String command, boolean require_auth) {
        final TextView garageTxt = (TextView)_parent.findViewById(R.id.garagedoor_status);
        final TextView manTxt = (TextView)_parent.findViewById(R.id.mandoor_status);
        final Button garageBtn = (Button) _parent.findViewById(R.id.garage_move);

        String commandURL = AutomationHelper.BASE_URL + command;
        commandURL += ( require_auth ? "/" + AutomationHelper.AUTH_CODE + "/" + AutomationHelper.USER_ID : "");

        JsonObjectRequest jsonRequest =
            new JsonObjectRequest(
                    Request.Method.GET,
                    commandURL,
                    null,
                    new Response.Listener<JSONObject>() {
                        @Override
                        public void onResponse(JSONObject response) {
                            if (response.has("items")) {
                                try {
                                    JSONArray items = response.getJSONArray("items");
                                    JSONObject item;
                                    for ( int i = 0; i < items.length(); i++){
                                        item = (JSONObject)items.get(i);
                                        String source = item.getString("source");
                                        if (source.equals("ManDoor")) {
                                            manTxt.setText("ManDoor: " + makeEventString(item));
                                        }

                                        if (source.equals("GarageDoor")) {
                                            garageTxt.setText("GarageDoor: " + makeEventString(item));
                                            isOpen = item.getString("event").equals("Open");
                                            garageBtn.setText((isOpen ? "Close" : "Open"));
                                        }
                                    }
                                } catch (JSONException jsex) {
                                    manTxt.setText("LOL ERROR (" + command + ")");
                                    garageTxt.setText("LOL ERROR (" + command + ")");
                                }
                            } else {
                                try {
                                    String source = response.getString("source");
                                    if (source.equals("ManDoor")) {
                                        manTxt.setText("ManDoor: " + makeEventString(response));
                                    }

                                    if (source.equals("GarageDoor")) {
                                        garageTxt.setText("GarageDoor: " + makeEventString(response));
                                        isOpen = response.getString("event").equals("Open");
                                        garageBtn.setText((isOpen ? "Close" : "Open"));
                                    }
                                    //TODO: This needs to be looked at. It won't function if the door doesn't actually close. We need to queue a refresh
                                    if (source.equals("Open")) {
                                        isOpen = response.getString("event").equals("Done");
                                    }
                                    if (source.equals("Close")) {
                                        isOpen = response.getString("event").equals("Done");
                                    }
                                }catch(JSONException jsex){
                                    manTxt.setText("LOL ERROR (" + command + ")");
                                    garageTxt.setText("LOL ERROR (" + command + ")");
                                }
                            }
                        }
                    },
                    new Response.ErrorListener() {
                        @Override
                        public void onErrorResponse(VolleyError error) {
                            manTxt.setText("LOL NETWORK ERROR");
                            garageTxt.setText("LOL NETWORK ERROR");
                        }
                    });

        _requests.add(jsonRequest);

        return true;
    }

    private String makeEventString(JSONObject jsonResponse) throws JSONException {
        String event = jsonResponse.getString("event");
        int duration = jsonResponse.getInt("duration");
        String time = jsonResponse.getString("time");

        return event + " @ " + time + " (" + String.valueOf(duration) + "sec)";
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == SPEECH_REQUEST_CODE && resultCode == Activity.RESULT_OK) {
            List<String> results = data.getStringArrayListExtra(
                    RecognizerIntent.EXTRA_RESULTS);
            if (results.get(0).equals("open garage door")) {
                sendGarageCommand("open",true);
            } else if (results.get(0).equals("close garage door")) {
                sendGarageCommand("close",true);
            } else if (results.get(0).equals("refresh")) {
                refresh();
            }
        }
        super.onActivityResult(requestCode, resultCode, data);
    }
}
