<?php
    if(isset($_GET['node'], $_GET['interface'])){
        $command = escapeshellcmd('python3 int-desc.py ' . $_GET['node'] . ' ' . $_GET['interface']);
        # var_dump($command);
        $output = trim(shell_exec($command));
        exit(json_encode(array('status' => 'ok', 'desc' => $output)));
    }
?><!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="author" content="Jonas Lindstad">
        <title>evpn-grep magic</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>

        <script>
            $(document).ready(function(){
                /* Fix interface description on "l2ng-l2-mac-logical-interface" */
                $('.filter-on-logical-interface').each(function(index){
                    var elem = $(this);
                    $.getJSON('?', {node: $(this).attr('data-node'), interface: $(this).text()})
                    .done(function(data){
                        console.log(data);
                        if(data.status == 'ok'){
                            elem.text(elem.text() + ' - ' + data['desc']);
                        }else{
                            console.log(data);
                        }
                    });
                });
            });
        </script>

    </head>
    <body class="container-md">
        <!--
            Jumbotron
        -->
        <div class="bg-light rounded-3 border my-4">
            <div class="container-fluid px-5 py-2 my-5">
                <h1 class="display-5 fw-bold mt-0">evpn-grep v0.1</h1>
                <p class="fs-4">Find (hourly cached) info from the IPfabric leaf switches regarding ethernet-switching and evpn database.</p>
                <p>If you expect to see more info than shown, wait a minute and try again. Data is purged from the database before it's inserted (bulk action).</p>
                <p>Sources: <kbd>show arp no-resolve</kbd>, <kbd>show ethernet-switching table</kbd, <kbd>show evpn database</kbd>, <kbd>show conf vlans</kbd> and <kbd>show conf routing-instance VS-EVPN-DC bridge-domains</kbd> on all "*.ipfab.*.leaf*" and "*.core.*" nodes.</p>
                <p>Search examples: "<a href="?q=2996">2996</a>", "<a href="?q=63:3b:e8">63:3b:e8</a>" or "<a href="?q=10.248.252.143">10.248.252.143</a>"</p>
                <p class="mb-0">System documentation/code: <a href="https://www.vegvesen.no/wiki/display/Drift/svvpautomate01+-+evpn-grep">wiki</a>
            </div>
        </div>
        
        <!--
            Form + display results
        -->
        <div class="bg-light rounded-3 border my-4">
            <div class="container-fluid px-5 py-2 my-5">
                <form class="row g-3" method="get" action="">
                    <div class="col-auto">
                        <label for="" class="visually-hidden">Query for...</label>
                        <input type="text" readonly class="form-control-plaintext" value="Query for...">
                    </div>
                    <div class="col-auto">
                        <label for="q" class="visually-hidden">q</label>
                        <input type="text" class="form-control" id="q" name="q" placeholder="VLAN, MAC, IP or VNI" value="<?php if(isset($_GET['q'])){echo htmlspecialchars($_GET['q']);} ?>">
                    </div>
                    <div class="col-auto">
                        <button type="submit" class="btn btn-primary">Search</button>
                    </div>
                </form>
            </div>
        </div>
        
        <?php
            #
            # To hilight text
            #
            function hilight($match, $string, $node){
                /*
                    Make stuff clickable and hilight "physical" logical interfaces
                    split into two sections, for optimization. Less lines to regex match against
                */
                if(strpos($string, 'l2ng-l2') !== false || strpos($string, 'l2-mac-') !== false){ # ethernet switching
                    $string = preg_replace(
                        array(
                            '/^l2ng-l2-mac-logical-interface: ([a-z]{2}[\-0-9].*)/m',
                            '/^l2ng-l2-mac-vlan-name: (.*)/m',
                            '/^l2ng-l2-mac-address: (.*)/m',
                            '/^l2-mac-address: (.*)/m',
                            '/^l2-bridge-vlan: (.*)/m'
                        ), array(
                            'l2ng-l2-mac-logical-interface: <span data-node="' . $node . '" class="filter-on-logical-interface bg-danger text-white">$1</span>',
                            'l2ng-l2-mac-vlan-name: <a href="?q=$1">$1</a>',
                            'l2ng-l2-mac-address: <a href="?q=$1">$1</a>',
                            'l2-mac-address: <a href="?q=$1">$1</a>',
                            'l2-bridge-vlan: <a href="?q=$1">$1</a>'
                        ),
                    $string);
                }elseif(strpos($string, 'interface-name') !== false){ # ARP
                    $string = preg_replace(
                        array(
                            '/ip-address: (.*)/',
                            '/mac-address: (.*)/'
                        ), array(
                            'ip-address: <a href="?q=$1">$1</a>',
                            'mac-address: <a href="?q=$1">$1</a>'
                        ),
                    $string);



                }elseif(strpos($string, 'conf-bd') !== false){ # conf-bd
                    $string = preg_replace(
                        array(
                            '/conf-bd-vlan-id: (.*)/',
                            '/conf-bd-vni: (.*)/',
                            '/conf-bd-routing-interface: (.*)/'
                        ), array(
                            'conf-bd-vlan-id: <a href="?q=$1">$1</a>',
                            'conf-bd-vni: <a href="?q=$1">$1</a>',
                            'conf-bd-routing-interface: <a href="?q=$1">$1</a>'
                        ),
                    $string);


                }elseif(strpos($string, 'conf-vlans') !== false){ # conf-vlans
                    $string = preg_replace(
                        array(
                            '/conf-vlans-vlan-id: (.*)/',
                            '/conf-vlans-vni: (.*)/'
                        ), array(
                            'conf-vlans-vlan-id: <a href="?q=$1">$1</a>',
                            'conf-vlans-vni: <a href="?q=$1">$1</a>'
                        ),
                    $string);





                }else{ # EVPN
                    $string = preg_replace(
                        array(
                            '/vni-id: ([0-9]*)/',
                            '/mac-address: (.*)/'
                        ), array(
                            'vni-id: <a href="?q=$1">$1</a>',
                            'mac-address: <a href="?q=$1">$1</a>'
                        ),
                    $string);
                }
                return $string;
            }
        
            /*
                If search has been performed
            */
            if(isset($_GET, $_GET['q'])){
                echo '
                    <div class="bg-light rounded-3 border my-4">
                        <div class="container-fluid px-5 py-2 my-5">
                ';
                $q = $_GET['q'];
                if(strlen($q) < 3){
                    echo 'Sorry, we need at least a query string lenght at 3 characters';
                }else{
                    echo '
                    
                    <table class="table">
                        <thead>
                            <tr>
                                <th scope="col">Node</th>
                                <th scope="col">Timestamp when data was collected</th>
                                <th scope="col">Source</th>
                                <th scope="col">Content</th>
                            </tr>
                        </thead>
                        <tbody>
                    ';
                    $db = new SQLite3('evpn.db');
                    
                    $results = $db->query('select * from data where content like "%' . SQLite3::escapeString($q) . '%";');
                    while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
                        echo '
                            <tr>
                                <th scope="row"><span style="white-space: nowrap;">' . $row['node'] . '</span></th>
                                <td>' . $row['date'] . '</td>
                                <td>' . $row['type'] . '</td>
                                <td>' . nl2br(hilight($q, $row['content'], $row['node'])) . '</td>
                            </tr>
                        ';
                    }
                    echo '
                        </tbody>
                    </table>
                    ';
                }
                
                echo '
                        </div> <!-- /. bg-light rounded-3 border mb-5 -->
                    </div> <!-- /. container-fluid px-5 py-2 my-5 -->
                ';
            }
        ?>
    </body>
</html>