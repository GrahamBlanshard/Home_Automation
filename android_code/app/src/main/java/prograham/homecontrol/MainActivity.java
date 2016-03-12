package prograham.homecontrol;

import android.app.Activity;
import android.app.FragmentManager;
import android.content.Intent;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.view.KeyEvent;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;

public class MainActivity extends AppCompatActivity {

    private GarageFragment garageFragment;

    /**
     * Called when the activity is first created.
     */
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        if (findViewById(R.id.main_container) != null) {
            if (savedInstanceState != null) {
                return;
            }

            garageFragment = new GarageFragment();
            garageFragment.setArguments(getIntent().getExtras());

            getFragmentManager().beginTransaction()
                    .add(R.id.main_container, garageFragment, "garage_fragment")
                    .commit();
        }
    }


    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle item selection
        switch (item.getItemId()) {
            case R.id.menu_quit:
                quit();
                return true;
            case R.id.menu_refresh:
                garageFragment.refresh();
                return true;
            default:
                return super.onOptionsItemSelected(item);
        }
    }

    /**
     * On quit print log message
     */
    @Override
    protected void onDestroy() {
        super.onDestroy();
    }

    /**
     * On halt, print log message
     */
    @Override
    protected void onStop() {
        super.onStop();
    }

    /**
     * Creates our main
     */
    public boolean onCreateOptionsMenu(Menu menu) {
        MenuInflater inflater = getMenuInflater();
        inflater.inflate(R.menu.garage_menu, menu);
        return true;
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK) {
            if (getFragmentManager().getBackStackEntryCount() == 0) {
                quit();
            } else {
                getFragmentManager().popBackStack(null, FragmentManager.POP_BACK_STACK_INCLUSIVE);
            }
            return true;
        } else if (keyCode == KeyEvent.KEYCODE_MENU) {
            openOptionsMenu();
            return true;
        }
        return false;
    }

    /**
     * Closes our application
     */
    private void quit() {
        Intent intent = new Intent();
        setResult(RESULT_OK, intent);

        finish();
    }
}
